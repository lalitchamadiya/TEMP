import csv
import json
from functools import wraps

from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from .decorators import role_required, permission_required
from .models import AuditLog, Module, Role, RolePermission, UserProfile

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log_action(actor, action, target_user=None, details='', request=None):
    """Utility to record an audit log entry."""
    ip = None
    if request:
        x_forward = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forward.split(',')[0] if x_forward else request.META.get('REMOTE_ADDR')
    AuditLog.objects.create(
        actor=actor,
        target_user=target_user,
        action=action,
        details=details,
        ip_address=ip,
    )


def get_client_ip(request):
    x_forward = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forward.split(',')[0] if x_forward else request.META.get('REMOTE_ADDR')


# ---------------------------------------------------------------------------
# Auth — Validation, Registration, Login, Logout
# ---------------------------------------------------------------------------

class EmailValidationView(View):
    def post(self, request):
        from validate_email import validate_email
        data = json.loads(request.body)
        email = data['email']
        if not validate_email(email):
            return JsonResponse({'email_error': 'Email is invalid'}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'email_error': 'Email already in use'}, status=409)
        return JsonResponse({'email_valid': True})


class UserNameValidationView(View):
    def post(self, request):
        data = json.loads(request.body)
        username = data['username']
        if not str(username).isalnum():
            return JsonResponse({'username_error': 'Username must be alphanumeric'}, status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({'username_error': 'Username already taken'}, status=409)
        return JsonResponse({'username_valid': True})


class RegistrationView(View):
    def get(self, request):
        roles = Role.objects.filter(is_active=True).exclude(is_superadmin=True)
        return render(request, 'authentication/register.html', {'roles': roles})

    def post(self, request):
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        role_id = request.POST['role']

        context = {
            'fieldValues': request.POST,
            'roles': Role.objects.filter(is_active=True).exclude(is_superadmin=True),
        }

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'authentication/register.html', context)
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'authentication/register.html', context)
        if len(password) < 6:
            messages.error(request, 'Password too short')
            return render(request, 'authentication/register.html', context)

        user = User.objects.create_user(username=username, email=email)
        user.set_password(password)
        user.save()

        try:
            role_obj = Role.objects.get(id=role_id)
            UserProfile.objects.create(user=user, role=role_obj)
            group, _ = Group.objects.get_or_create(name=role_obj.name)
            group.user_set.add(user)
        except (Role.DoesNotExist, ValueError):
            student_role = Role.objects.filter(name='Student').first()
            if student_role:
                UserProfile.objects.create(user=user, role=student_role)

        messages.success(request, 'Account Successfully Created')
        return redirect('login')


class LoginView(View):
    def get(self, request):
        return render(request, 'authentication/login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']

        if username and password:
            user = auth.authenticate(username=username, password=password)
            if user:
                # Check if account is locked
                if hasattr(user, 'profile') and user.profile.is_locked:
                    messages.error(request, 'Your account has been locked. Contact an administrator.')
                    return render(request, 'authentication/login.html')

                if user.is_active:
                    auth.login(request, user)
                    request.session.set_expiry(900)
                    log_action(user, 'login', user, request=request)

                    if hasattr(user, 'profile') and user.profile.role:
                        role_name = user.profile.role.name
                        if role_name in ('Super Admin', 'Admin'):
                            return redirect('superadmin_dashboard')
                        elif role_name == 'Student':
                            return redirect('student_app:student_dashboard')
                        elif role_name == 'Warden':
                            return redirect('warden_dashboard')
                        elif role_name == 'Staff':
                            return redirect('superadmin_dashboard')
                    return redirect('superadmin_dashboard')

                messages.error(request, 'Account is not active')
                return render(request, 'authentication/login.html')

            messages.error(request, 'Invalid credentials, try again')
            return render(request, 'authentication/login.html')

        messages.error(request, 'Please fill all fields')
        return render(request, 'authentication/login.html')


class LogoutView(View):
    def post(self, request):
        if request.user.is_authenticated:
            log_action(request.user, 'logout', request.user, request=request)
        auth.logout(request)
        messages.success(request, 'You have been logged out')
        return redirect('login')


# ---------------------------------------------------------------------------
# Role Management
# ---------------------------------------------------------------------------

@login_required
@role_required('Super Admin')
def role_list(request):
    roles = Role.objects.all().order_by('-created_at')
    return render(request, 'authentication/rbac/role_list.html', {'roles': roles})


@login_required
@role_required('Super Admin')
def role_create(request):
    modules = Module.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'

        role = Role.objects.create(name=name, description=description, is_active=is_active)

        for module in modules:
            RolePermission.objects.create(
                role=role, module=module,
                can_view=request.POST.get(f'view_{module.id}') == 'on',
                can_add=request.POST.get(f'add_{module.id}') == 'on',
                can_edit=request.POST.get(f'edit_{module.id}') == 'on',
                can_delete=request.POST.get(f'delete_{module.id}') == 'on',
                can_approve=request.POST.get(f'approve_{module.id}') == 'on',
                can_reject=request.POST.get(f'reject_{module.id}') == 'on',
                can_export=request.POST.get(f'export_{module.id}') == 'on',
                can_print=request.POST.get(f'print_{module.id}') == 'on',
                can_import=request.POST.get(f'import_{module.id}') == 'on',
                can_hide=request.POST.get(f'hide_{module.id}') == 'on',
                can_disable=request.POST.get(f'disable_{module.id}') == 'on',
            )

        messages.success(request, f"Role '{name}' created successfully.")
        return redirect('role_list')

    return render(request, 'authentication/rbac/role_form.html', {'modules': modules, 'role_perms': {}})


@login_required
@role_required('Super Admin')
def role_edit(request, pk):
    role = get_object_or_404(Role, pk=pk)
    modules = Module.objects.all()

    if request.method == 'POST':
        role.name = request.POST.get('name')
        role.description = request.POST.get('description')
        role.is_active = request.POST.get('is_active') == 'on'
        role.save()

        for module in modules:
            perm, _ = RolePermission.objects.get_or_create(role=role, module=module)
            perm.can_view = request.POST.get(f'view_{module.id}') == 'on'
            perm.can_add = request.POST.get(f'add_{module.id}') == 'on'
            perm.can_edit = request.POST.get(f'edit_{module.id}') == 'on'
            perm.can_delete = request.POST.get(f'delete_{module.id}') == 'on'
            perm.can_approve = request.POST.get(f'approve_{module.id}') == 'on'
            perm.can_reject = request.POST.get(f'reject_{module.id}') == 'on'
            perm.can_export = request.POST.get(f'export_{module.id}') == 'on'
            perm.can_print = request.POST.get(f'print_{module.id}') == 'on'
            perm.can_import = request.POST.get(f'import_{module.id}') == 'on'
            perm.can_hide = request.POST.get(f'hide_{module.id}') == 'on'
            perm.can_disable = request.POST.get(f'disable_{module.id}') == 'on'
            perm.save()

        messages.success(request, f"Role '{role.name}' updated successfully.")
        return redirect('role_list')

    role_perms = {p.module_id: p for p in role.permissions.all()}
    return render(request, 'authentication/rbac/role_form.html', {
        'role': role, 'modules': modules, 'role_perms': role_perms
    })


@login_required
@role_required('Super Admin')
def role_clone(request, pk):
    """Deep copy of a role's permissions to a new role."""
    if request.method == 'POST':
        source_role = get_object_or_404(Role, pk=pk)
        new_name = request.POST.get('name', f"{source_role.name} (Copy)").strip()
        
        if Role.objects.filter(name=new_name).exists():
            messages.error(request, f"A role named '{new_name}' already exists.")
            return redirect('role_list')
            
        new_role = Role.objects.create(
            name=new_name,
            description=f"Cloned from '{source_role.name}'. {source_role.description}",
            is_active=source_role.is_active
        )
        
        # Copy permissions
        for perm in source_role.permissions.all():
            RolePermission.objects.create(
                role=new_role,
                module=perm.module,
                can_view=perm.can_view,
                can_add=perm.can_add,
                can_edit=perm.can_edit,
                can_delete=perm.can_delete,
                can_approve=perm.can_approve,
                can_reject=perm.can_reject,
                can_export=perm.can_export,
                can_print=perm.can_print,
                can_import=perm.can_import,
                can_hide=perm.can_hide,
                can_disable=perm.can_disable,
            )
            
        log_action(request.user, 'create', None, f"Cloned role '{source_role.name}' to '{new_role.name}'", request)
        messages.success(request, f"Role '{source_role.name}' cloned to '{new_role.name}' successfully.")
    return redirect('role_list')


@login_required
def permission_overview(request, pk):
    """Returns JSON of a user's permissions."""
    target_user = get_object_or_404(User, pk=pk)
    if request.user.id != target_user.id and not (
        request.user.is_superuser or (
            hasattr(request.user, 'profile') and
            request.user.profile.role and
            request.user.profile.role.is_superadmin
        )
    ):
        return JsonResponse({'error': 'Forbidden'}, status=403)
        
    from .context_processors import rbac_context
    class FakeRequest:
        def __init__(self, user):
            self.user = user
            self.session = {}
    fake_req = FakeRequest(target_user)
    ctx = rbac_context(fake_req)
    return JsonResponse(ctx)


@login_required
@role_required('Super Admin')
def role_delete(request, pk):
    role = get_object_or_404(Role, pk=pk)
    if role.is_superadmin:
        messages.error(request, 'Super Admin role cannot be deleted.')
    else:
        role.delete()
        messages.success(request, 'Role deleted successfully.')
    return redirect('role_list')


# ---------------------------------------------------------------------------
# User Management — Full CRUD + Actions
# ---------------------------------------------------------------------------

@login_required
@role_required('Super Admin')
def user_list(request):
    """Redirect User Management to Staff Management list."""
    return redirect('staff_list')


@login_required
@role_required('Super Admin')
def user_create(request):
    """Create a new user account with full profile details."""
    roles = Role.objects.filter(is_active=True)
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        role_id = request.POST.get('role')
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        is_active = request.POST.get('is_active', 'on') == 'on'

        errors = []
        if not username:
            errors.append('Username is required.')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        if email and User.objects.filter(email=email).exists():
            errors.append('Email already in use.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'authentication/rbac/user_form.html', {
                'roles': roles, 'form_data': request.POST
            })

        user = User.objects.create_user(
            username=username, email=email,
            first_name=first_name, last_name=last_name,
        )
        user.set_password(password)
        user.is_active = is_active
        user.save()

        # Build profile
        profile = UserProfile.objects.create(user=user, phone=phone)
        if role_id:
            try:
                role_obj = Role.objects.get(id=role_id)
                profile.role = role_obj
                group, _ = Group.objects.get_or_create(name=role_obj.name)
                group.user_set.add(user)
            except Role.DoesNotExist:
                pass
        if request.FILES.get('photo'):
            profile.photo = request.FILES['photo']
        profile.save()

        log_action(request.user, 'create', user, f'Created user {username}', request)
        messages.success(request, f"User '{username}' created successfully.")
        return redirect('user_management')

    return render(request, 'authentication/rbac/user_form.html', {'roles': roles})


@login_required
@role_required('Super Admin')
def user_detail(request, pk):
    """View full user profile and audit history."""
    target = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=target)
    audit_logs = AuditLog.objects.filter(target_user=target).select_related('actor')[:50]
    return render(request, 'authentication/rbac/user_detail.html', {
        'target': target,
        'profile': profile,
        'audit_logs': audit_logs,
    })


@login_required
@role_required('Super Admin')
def user_edit(request, pk):
    """Edit an existing user's information."""
    target = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=target)
    roles = Role.objects.filter(is_active=True)

    if request.method == 'POST':
        target.first_name = request.POST.get('first_name', '').strip()
        target.last_name = request.POST.get('last_name', '').strip()
        target.email = request.POST.get('email', '').strip()
        target.is_active = request.POST.get('is_active') == 'on'
        target.save()

        profile.phone = request.POST.get('phone', '').strip()
        if request.FILES.get('photo'):
            profile.photo = request.FILES['photo']

        role_id = request.POST.get('role')
        if role_id:
            try:
                new_role = Role.objects.get(id=role_id)
                old_role = profile.role.name if profile.role else 'None'
                profile.role = new_role
                target.groups.clear()
                group, _ = Group.objects.get_or_create(name=new_role.name)
                target.groups.add(group)
                if old_role != new_role.name:
                    log_action(request.user, 'role_change', target,
                               f'Role changed from {old_role} to {new_role.name}', request)
            except Role.DoesNotExist:
                pass
        profile.save()

        log_action(request.user, 'edit', target, f'Edited user {target.username}', request)
        messages.success(request, f"User '{target.username}' updated successfully.")
        return redirect('user_detail', pk=pk)

    return render(request, 'authentication/rbac/user_form.html', {
        'roles': roles,
        'target': target,
        'profile': profile,
        'edit_mode': True,
    })


@login_required
@role_required('Super Admin')
def user_delete(request, pk):
    """Confirm and delete a user account."""
    target = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if target.id == request.user.id:
            messages.error(request, 'You cannot delete your own account.')
            return redirect('user_management')
        username = target.username
        log_action(request.user, 'delete', None, f'Deleted user {username}', request)
        target.delete()
        messages.success(request, f"User '{username}' has been deleted.")
        return redirect('user_management')

    return render(request, 'authentication/rbac/user_confirm_delete.html', {'target': target})


@login_required
@role_required('Super Admin')
def user_toggle_status(request, pk):
    """Activate or deactivate a user account."""
    if request.method == 'POST':
        target = get_object_or_404(User, pk=pk)
        if target.id == request.user.id:
            messages.error(request, 'You cannot deactivate your own account.')
            return redirect('user_management')
        target.is_active = not target.is_active
        target.save()
        action = 'activate' if target.is_active else 'deactivate'
        log_action(request.user, action, target, f'Account {"activated" if target.is_active else "deactivated"}', request)
        messages.success(request, f"User '{target.username}' has been {'activated' if target.is_active else 'deactivated'}.")
    return redirect('user_management')


@login_required
@role_required('Super Admin')
def user_lock(request, pk):
    """Lock or unlock a user account."""
    if request.method == 'POST':
        target = get_object_or_404(User, pk=pk)
        if target.id == request.user.id:
            messages.error(request, 'You cannot lock your own account.')
            return redirect('user_management')
        profile, _ = UserProfile.objects.get_or_create(user=target)
        profile.is_locked = not profile.is_locked
        profile.save()
        action = 'lock' if profile.is_locked else 'unlock'
        log_action(request.user, action, target, f'Account {"locked" if profile.is_locked else "unlocked"}', request)
        messages.success(request, f"User '{target.username}' has been {'locked' if profile.is_locked else 'unlocked'}.")
    return redirect('user_management')


@login_required
@role_required('Super Admin')
def user_reset_password(request, pk):
    """Reset a user's password to a new value provided by the Super Admin."""
    target = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not new_password or len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
        elif new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        else:
            target.set_password(new_password)
            target.save()
            log_action(request.user, 'password_reset', target, f'Password reset for {target.username}', request)
            messages.success(request, f"Password for '{target.username}' has been reset successfully.")
            return redirect('user_management')

    return render(request, 'authentication/rbac/user_reset_password.html', {'target': target})


@login_required
@role_required('Super Admin')
def user_change_role(request, pk):
    """Change a user's role via modal POST."""
    if request.method == 'POST':
        target = get_object_or_404(User, pk=pk)
        role_id = request.POST.get('role_id')
        if role_id:
            role = get_object_or_404(Role, id=role_id)
            profile, _ = UserProfile.objects.get_or_create(user=target)
            old_role = profile.role.name if profile.role else 'None'
            profile.role = role
            profile.save()
            target.groups.clear()
            group, _ = Group.objects.get_or_create(name=role.name)
            target.groups.add(group)
            log_action(request.user, 'role_change', target,
                       f'Role changed from {old_role} to {role.name}', request)
            messages.success(request, f"Role updated for '{target.username}'.")
    return redirect('user_management')


@login_required
@role_required('Super Admin')
def user_export(request):
    """Export filtered user list as CSV."""
    qs = User.objects.select_related('profile', 'profile__role').order_by('username')
    selected_ids = request.GET.getlist('ids')
    if selected_ids:
        qs = qs.filter(id__in=selected_ids)

    log_action(request.user, 'export', None, f'Exported {qs.count()} user records', request)
    return _export_users_csv(qs)


def _export_users_csv(queryset):
    """Internal helper — stream a CSV response for a User queryset."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Username', 'Full Name', 'Email', 'Phone', 'Role', 'Status', 'Locked', 'Date Joined', 'Last Login'])
    for u in queryset:
        profile = getattr(u, 'profile', None)
        writer.writerow([
            u.id,
            u.username,
            u.get_full_name(),
            u.email,
            profile.phone if profile else '',
            profile.role.name if profile and profile.role else 'No Role',
            'Active' if u.is_active else 'Inactive',
            'Yes' if profile and profile.is_locked else 'No',
            u.date_joined.strftime('%Y-%m-%d %H:%M'),
            u.last_login.strftime('%Y-%m-%d %H:%M') if u.last_login else 'Never',
        ])
    return response


@login_required
@role_required('Super Admin')
def user_audit(request, pk):
    """View the full audit log for a specific user."""
    target = get_object_or_404(User, pk=pk)
    logs = AuditLog.objects.filter(
        Q(target_user=target) | Q(actor=target)
    ).select_related('actor', 'target_user').order_by('-timestamp')
    return render(request, 'authentication/rbac/user_audit.html', {
        'target': target,
        'logs': logs,
    })


# Old alias kept for backward-compat from existing sidebar link
@login_required
@role_required('Super Admin')
def user_update_role(request, user_id):
    """Legacy endpoint — delegates to user_change_role."""
    return user_change_role(request, pk=user_id)
