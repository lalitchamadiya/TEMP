from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.models import User, Group
from authentication.models import UserProfile, Role

from .models import (
    Organization, SubscriptionPlan, OrganizationSubscription,
    WhiteLabelConfig, SupportTicket, OrganizationSettings
)


# ─── Permission helper ────────────────────────────────────────────────────────

def _require_superadmin(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    if request.user.is_superuser:
        return
    try:
        if request.user.profile.role and request.user.profile.role.is_superadmin:
            return
    except Exception:
        pass
    raise PermissionDenied


# ─── Organization CRUD ────────────────────────────────────────────────────────

@login_required
def org_list(request):
    _require_superadmin(request)
    orgs = Organization.objects.prefetch_related(
        'subscriptions__plan', 'hostels'
    ).annotate(
        hostel_count=Count('hostels', distinct=True),
        student_count=Count('students', distinct=True),
    ).order_by('name')

    context = {
        'orgs': orgs,
        'total': orgs.count(),
        'active': orgs.filter(is_active=True).count(),
        'page_title': 'Organization Management',
    }
    return render(request, 'organizations/org_list.html', context)


@login_required
def org_create(request):
    _require_superadmin(request)
    plans = SubscriptionPlan.objects.filter(is_active=True)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        plan_id = request.POST.get('plan')
        admin_username = request.POST.get('admin_username', '').strip()
        admin_email = request.POST.get('admin_email', '').strip()
        admin_password = request.POST.get('admin_password', '').strip()

        errors = []
        if not name:
            errors.append('Organization name is required.')
        elif Organization.objects.filter(name=name).exists():
            errors.append('An organization with this name already exists.')

        if not plan_id:
            errors.append('Subscription plan selection is compulsory.')

        if not admin_username:
            errors.append('Administrator username is required.')
        elif User.objects.filter(username=admin_username).exists():
            errors.append('Administrator username is already taken.')

        if not admin_email:
            errors.append('Administrator email is required.')
        elif User.objects.filter(email=admin_email).exists():
            errors.append('Administrator email is already taken.')

        if not admin_password:
            errors.append('Administrator password is required.')

        subdomain = request.POST.get('subdomain', '').strip() or None
        if subdomain and Organization.objects.filter(subdomain=subdomain).exists():
            errors.append('This subdomain is already taken.')

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'organizations/org_form.html', {
                'action': 'Create', 'plans': plans, 'post': request.POST
            })

        # Create new organization in pending state (is_active=False)
        org = Organization.objects.create(
            name=name,
            org_type=request.POST.get('org_type', 'university'),
            address=request.POST.get('address', ''),
            contact_email=request.POST.get('contact_email', ''),
            contact_phone=request.POST.get('contact_phone', ''),
            website=request.POST.get('website', ''),
            subdomain=subdomain,
            custom_domain=request.POST.get('custom_domain', ''),
            timezone=request.POST.get('timezone', 'Asia/Kolkata'),
            currency=request.POST.get('currency', 'INR'),
            language=request.POST.get('language', 'en'),
            primary_color=request.POST.get('primary_color', '#6366f1'),
            secondary_color=request.POST.get('secondary_color', '#0d6efd'),
            is_active=False,
        )
        if 'logo' in request.FILES:
            org.logo = request.FILES['logo']
            org.save()

        # Auto-create settings & white-label branding
        OrganizationSettings.objects.get_or_create(organization=org)
        WhiteLabelConfig.objects.get_or_create(
            organization=org,
            defaults={
                'primary_color': org.primary_color,
                'secondary_color': org.secondary_color,
            }
        )

        # Autoprovision admin account
        admin_user = User.objects.create_user(
            username=admin_username,
            email=admin_email,
            password=admin_password
        )
        
        # Seed core roles
        for rname, desc in [
            ('Admin', 'Organization Administrator'),
            ('Warden', 'Hostel Warden / Manager'),
            ('Student', 'Hostel Resident / Student'),
            ('Staff', 'Hostel Support Staff'),
        ]:
            Role.objects.get_or_create(name=rname, defaults={'description': desc})
            
        admin_role = Role.objects.get(name='Admin')
        UserProfile.objects.create(
            user=admin_user,
            role=admin_role,
            organization=org
        )

        # Create billing subscription record
        plan = get_object_or_404(SubscriptionPlan, pk=plan_id)
        OrganizationSubscription.objects.create(
            organization=org,
            plan=plan,
            is_active=False,
            payment_status='pending'
        )

        messages.success(request, f'Organization "{org.name}" created successfully. Credentials generated for administrator account.')
        return redirect('org_list')

    return render(request, 'organizations/org_form.html', {'action': 'Create', 'plans': plans})


@login_required
def org_edit(request, pk):
    _require_superadmin(request)
    org = get_object_or_404(Organization, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Organization name is required.')
            return render(request, 'organizations/org_form.html', {'action': 'Edit', 'org': org})

        subdomain = request.POST.get('subdomain', '').strip() or None
        if subdomain and Organization.objects.filter(subdomain=subdomain).exclude(pk=pk).exists():
            messages.error(request, 'This subdomain is already taken.')
            return render(request, 'organizations/org_form.html', {'action': 'Edit', 'org': org})

        org.name = name
        org.org_type = request.POST.get('org_type', org.org_type)
        org.address = request.POST.get('address', '')
        org.contact_email = request.POST.get('contact_email', '')
        org.contact_phone = request.POST.get('contact_phone', '')
        org.website = request.POST.get('website', '')
        org.subdomain = subdomain
        org.custom_domain = request.POST.get('custom_domain', '')
        org.timezone = request.POST.get('timezone', org.timezone)
        org.currency = request.POST.get('currency', org.currency)
        org.language = request.POST.get('language', org.language)
        org.primary_color = request.POST.get('primary_color', org.primary_color)
        org.secondary_color = request.POST.get('secondary_color', org.secondary_color)
        org.is_active = request.POST.get('is_active') == 'on'
        if 'logo' in request.FILES:
            org.logo = request.FILES['logo']
        org.save()

        messages.success(request, f'Organization "{org.name}" updated.')
        return redirect('org_list')

    return render(request, 'organizations/org_form.html', {'action': 'Edit', 'org': org})


@login_required
def org_delete(request, pk):
    _require_superadmin(request)
    org = get_object_or_404(Organization, pk=pk)

    if request.method == 'POST':
        name = org.name
        
        # 1. Clean up associated Django Users of this organization
        users_to_delete = User.objects.filter(profile__organization=org)
        users_to_delete.delete()
        
        # 2. Clean up hotels and cascaded data
        from authentication.models import Hostel
        Hostel.objects.filter(organization=org).delete()
        
        # 3. Clean up any remaining block/building/floor structures
        from room.models import HostelBuilding, HostelBlock
        HostelBuilding.objects.filter(organization=org).delete()
        HostelBlock.objects.filter(organization=org).delete()
        
        # 4. Delete the organization itself
        org.delete()
        messages.success(request, f'Organization "{name}" and all associated data deleted successfully.')
        return redirect('org_list')

    return render(request, 'organizations/org_confirm_delete.html', {'org': org})


@login_required
def org_toggle_status(request, pk):
    _require_superadmin(request)
    org = get_object_or_404(Organization, pk=pk)
    org.is_active = not org.is_active
    org.save()
    status = 'activated' if org.is_active else 'deactivated'
    messages.success(request, f'Organization "{org.name}" {status}.')
    return redirect('org_list')


@login_required
def org_detail(request, pk):
    _require_superadmin(request)
    org = get_object_or_404(Organization, pk=pk)
    subscription = org.subscriptions.filter(is_active=True).select_related('plan').first()
    settings_obj, _ = OrganizationSettings.objects.get_or_create(organization=org)
    users = User.objects.filter(profile__organization=org).select_related('profile__role')

    try:
        whitelabel = org.whitelabel
    except WhiteLabelConfig.DoesNotExist:
        whitelabel = None

    context = {
        'org': org,
        'subscription': subscription,
        'settings_obj': settings_obj,
        'whitelabel': whitelabel,
        'hostels': org.hostels.all(),
        'users': users,
        'ticket_count': org.support_tickets.filter(status__in=['open', 'in_progress']).count(),
        'page_title': f'Organization: {org.name}',
    }
    return render(request, 'organizations/org_detail.html', context)


# ─── Subscription Plans ───────────────────────────────────────────────────────

@login_required
def plan_list(request):
    _require_superadmin(request)
    plans = SubscriptionPlan.objects.annotate(
        subscriber_count=Count('subscriptions', filter=Q(subscriptions__is_active=True))
    ).order_by('monthly_price')
    return render(request, 'organizations/plan_list.html', {
        'plans': plans,
        'page_title': 'Subscription Plans',
    })


@login_required
def plan_create(request):
    _require_superadmin(request)
    if request.method == 'POST':
        plan = SubscriptionPlan.objects.create(
            name=request.POST.get('name', ''),
            tier=request.POST.get('tier', 'basic'),
            description=request.POST.get('description', ''),
            max_hostels=int(request.POST.get('max_hostels', 1)),
            max_students=int(request.POST.get('max_students', 100)),
            max_staff=int(request.POST.get('max_staff', 10)),
            storage_gb=int(request.POST.get('storage_gb', 5)),
            has_api_access=request.POST.get('has_api_access') == 'on',
            has_ai_features=request.POST.get('has_ai_features') == 'on',
            has_white_label=request.POST.get('has_white_label') == 'on',
            has_mobile_app=request.POST.get('has_mobile_app') == 'on',
            has_advanced_analytics=request.POST.get('has_advanced_analytics') == 'on',
            has_biometric_integration=request.POST.get('has_biometric_integration') == 'on',
            has_rfid_support=request.POST.get('has_rfid_support') == 'on',
            monthly_price=request.POST.get('monthly_price', 0),
            annual_price=request.POST.get('annual_price', 0),
            is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, f'Plan "{plan.name}" created.')
        return redirect('plan_list')
    return render(request, 'organizations/plan_form.html', {'action': 'Create'})


@login_required
def plan_edit(request, pk):
    _require_superadmin(request)
    plan = get_object_or_404(SubscriptionPlan, pk=pk)
    if request.method == 'POST':
        plan.name = request.POST.get('name', plan.name)
        plan.tier = request.POST.get('tier', plan.tier)
        plan.description = request.POST.get('description', plan.description)
        plan.max_hostels = int(request.POST.get('max_hostels', plan.max_hostels))
        plan.max_students = int(request.POST.get('max_students', plan.max_students))
        plan.max_staff = int(request.POST.get('max_staff', plan.max_staff))
        plan.storage_gb = int(request.POST.get('storage_gb', plan.storage_gb))
        plan.has_api_access = request.POST.get('has_api_access') == 'on'
        plan.has_ai_features = request.POST.get('has_ai_features') == 'on'
        plan.has_white_label = request.POST.get('has_white_label') == 'on'
        plan.has_mobile_app = request.POST.get('has_mobile_app') == 'on'
        plan.has_advanced_analytics = request.POST.get('has_advanced_analytics') == 'on'
        plan.has_biometric_integration = request.POST.get('has_biometric_integration') == 'on'
        plan.has_rfid_support = request.POST.get('has_rfid_support') == 'on'
        plan.monthly_price = request.POST.get('monthly_price', plan.monthly_price)
        plan.annual_price = request.POST.get('annual_price', plan.annual_price)
        plan.is_active = request.POST.get('is_active') == 'on'
        plan.save()
        messages.success(request, f'Plan "{plan.name}" updated.')
        return redirect('plan_list')
    return render(request, 'organizations/plan_form.html', {'action': 'Edit', 'plan': plan})


@login_required
def plan_delete(request, pk):
    _require_superadmin(request)
    plan = get_object_or_404(SubscriptionPlan, pk=pk)
    if plan.subscriptions.filter(is_active=True).exists():
        messages.error(request, 'Cannot delete a plan with active subscribers.')
        return redirect('plan_list')
    if request.method == 'POST':
        name = plan.name
        plan.delete()
        messages.success(request, f'Plan "{name}" deleted.')
        return redirect('plan_list')
    return render(request, 'organizations/plan_confirm_delete.html', {'plan': plan})


# ─── Subscriptions ────────────────────────────────────────────────────────────

@login_required
def subscription_list(request):
    _require_superadmin(request)
    subs = OrganizationSubscription.objects.select_related('organization', 'plan').order_by(
        '-created_at'
    )
    return render(request, 'organizations/subscription_list.html', {
        'subs': subs,
        'page_title': 'Subscriptions',
    })


@login_required
def assign_subscription(request):
    _require_superadmin(request)
    orgs = Organization.objects.filter(is_active=True)
    plans = SubscriptionPlan.objects.filter(is_active=True)

    if request.method == 'POST':
        org = get_object_or_404(Organization, pk=request.POST.get('organization'))
        plan = get_object_or_404(SubscriptionPlan, pk=request.POST.get('plan'))

        # Deactivate previous active subscriptions
        OrganizationSubscription.objects.filter(
            organization=org, is_active=True
        ).update(is_active=False)

        sub = OrganizationSubscription.objects.create(
            organization=org,
            plan=plan,
            start_date=request.POST.get('start_date') or timezone.now().date(),
            end_date=request.POST.get('end_date') or None,
            is_active=True,
            payment_status=request.POST.get('payment_status', 'trial'),
            invoice_number=request.POST.get('invoice_number', ''),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, f'Subscription assigned: {org.name} → {plan.name}')
        return redirect('subscription_list')

    return render(request, 'organizations/assign_subscription.html', {
        'orgs': orgs,
        'plans': plans,
        'page_title': 'Assign Subscription',
    })


@login_required
def cancel_subscription(request, pk):
    _require_superadmin(request)
    sub = get_object_or_404(OrganizationSubscription, pk=pk)
    if request.method == 'POST':
        sub.is_active = False
        sub.payment_status = 'cancelled'
        sub.save()
        messages.success(request, f'Subscription for {sub.organization.name} cancelled.')
        return redirect('subscription_list')
    return render(request, 'organizations/sub_confirm_cancel.html', {'sub': sub})


# ─── White Label ──────────────────────────────────────────────────────────────

@login_required
def whitelabel_config(request, org_pk):
    _require_superadmin(request)
    org = get_object_or_404(Organization, pk=org_pk)
    config, _ = WhiteLabelConfig.objects.get_or_create(organization=org)

    if request.method == 'POST':
        config.primary_color = request.POST.get('primary_color', config.primary_color)
        config.secondary_color = request.POST.get('secondary_color', config.secondary_color)
        config.accent_color = request.POST.get('accent_color', config.accent_color)
        config.login_tagline = request.POST.get('login_tagline', config.login_tagline)
        config.footer_text = request.POST.get('footer_text', config.footer_text)
        config.report_header = request.POST.get('report_header', config.report_header)
        config.custom_css = request.POST.get('custom_css', config.custom_css)
        if 'logo' in request.FILES:
            config.logo = request.FILES['logo']
        if 'favicon' in request.FILES:
            config.favicon = request.FILES['favicon']
        if 'login_background' in request.FILES:
            config.login_background = request.FILES['login_background']
        config.save()
        messages.success(request, 'White Label settings saved.')
        return redirect('org_detail', pk=org_pk)

    return render(request, 'organizations/whitelabel_form.html', {
        'org': org,
        'config': config,
        'page_title': f'White Label — {org.name}',
    })


# ─── Global Analytics ─────────────────────────────────────────────────────────

@login_required
def global_analytics(request):
    _require_superadmin(request)
    from authentication.models import Hostel
    from student.models import Student

    orgs = Organization.objects.annotate(
        h_count=Count('hostels', distinct=True),
        s_count=Count('students', distinct=True),
    )

    context = {
        'page_title': 'Global Analytics',
        'total_orgs': Organization.objects.count(),
        'active_orgs': Organization.objects.filter(is_active=True).count(),
        'total_hostels': Hostel.objects.count(),
        'total_students': Student.objects.count(),
        'active_students': Student.objects.filter(status='Active').count(),
        'total_subscriptions': OrganizationSubscription.objects.filter(is_active=True).count(),
        'orgs': orgs,
        'plan_stats': SubscriptionPlan.objects.annotate(
            active_subs=Count('subscriptions', filter=Q(subscriptions__is_active=True))
        ),
    }
    return render(request, 'organizations/global_analytics.html', context)


# ─── Revenue Dashboard ────────────────────────────────────────────────────────

@login_required
def revenue_dashboard(request):
    _require_superadmin(request)
    active_subs = OrganizationSubscription.objects.filter(
        is_active=True
    ).select_related('organization', 'plan')

    monthly_revenue = sum(
        s.plan.monthly_price for s in active_subs
        if s.payment_status == 'active'
    )
    annual_revenue = sum(
        s.plan.annual_price for s in active_subs
        if s.payment_status == 'active'
    )

    context = {
        'page_title': 'Revenue Dashboard',
        'active_subs': active_subs,
        'monthly_revenue': monthly_revenue,
        'annual_revenue': annual_revenue,
        'total_active': active_subs.count(),
        'by_plan': SubscriptionPlan.objects.annotate(
            count=Count('subscriptions', filter=Q(subscriptions__is_active=True)),
        ).order_by('-count'),
    }
    return render(request, 'organizations/revenue_dashboard.html', context)


# ─── Support Tickets ──────────────────────────────────────────────────────────

@login_required
def support_ticket_list(request):
    _require_superadmin(request)
    tickets = SupportTicket.objects.select_related(
        'organization', 'raised_by', 'assigned_to'
    ).order_by('-created_at')

    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)

    context = {
        'tickets': tickets,
        'open_count': SupportTicket.objects.filter(status='open').count(),
        'in_progress_count': SupportTicket.objects.filter(status='in_progress').count(),
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'page_title': 'Support Tickets',
    }
    return render(request, 'organizations/support_ticket_list.html', context)


@login_required
def support_ticket_create(request):
    orgs = Organization.objects.filter(is_active=True)
    if request.method == 'POST':
        org = get_object_or_404(Organization, pk=request.POST.get('organization'))
        ticket = SupportTicket.objects.create(
            organization=org,
            raised_by=request.user,
            title=request.POST.get('title', ''),
            description=request.POST.get('description', ''),
            category=request.POST.get('category', 'technical'),
            priority=request.POST.get('priority', 'medium'),
        )
        messages.success(request, f'Ticket #{ticket.id} submitted.')
        return redirect('support_ticket_list')
    return render(request, 'organizations/support_ticket_form.html', {
        'orgs': orgs,
        'page_title': 'New Support Ticket',
    })


@login_required
def support_ticket_detail(request, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk)
    return render(request, 'organizations/support_ticket_detail.html', {
        'ticket': ticket,
        'page_title': f'Ticket #{ticket.id}',
    })


@login_required
def support_ticket_update(request, pk):
    _require_superadmin(request)
    ticket = get_object_or_404(SupportTicket, pk=pk)
    if request.method == 'POST':
        ticket.status = request.POST.get('status', ticket.status)
        ticket.priority = request.POST.get('priority', ticket.priority)
        ticket.resolution_notes = request.POST.get('resolution_notes', ticket.resolution_notes)
        if ticket.status in ('resolved', 'closed') and not ticket.resolved_at:
            ticket.resolved_at = timezone.now()
        assigned_id = request.POST.get('assigned_to')
        if assigned_id:
            from django.contrib.auth.models import User
            ticket.assigned_to = User.objects.filter(pk=assigned_id).first()
        ticket.save()
        messages.success(request, f'Ticket #{ticket.id} updated.')
        return redirect('support_ticket_detail', pk=pk)
    return redirect('support_ticket_detail', pk=pk)


# ─── Organization Settings ────────────────────────────────────────────────────

@login_required
def org_settings(request, org_pk):
    _require_superadmin(request)
    org = get_object_or_404(Organization, pk=org_pk)
    settings_obj, _ = OrganizationSettings.objects.get_or_create(organization=org)

    if request.method == 'POST':
        import json
        settings_obj.current_academic_year = request.POST.get(
            'current_academic_year', settings_obj.current_academic_year
        )
        settings_obj.fee_policy = request.POST.get('fee_policy', settings_obj.fee_policy)
        settings_obj.attendance_policy = request.POST.get(
            'attendance_policy', settings_obj.attendance_policy
        )
        settings_obj.visitor_policy = request.POST.get(
            'visitor_policy', settings_obj.visitor_policy
        )
        settings_obj.leave_policy = request.POST.get('leave_policy', settings_obj.leave_policy)
        settings_obj.hostel_rules = request.POST.get('hostel_rules', settings_obj.hostel_rules)

        # JSON fields from textarea (newline-separated)
        departments_raw = request.POST.get('departments', '')
        if departments_raw:
            settings_obj.departments = [d.strip() for d in departments_raw.splitlines() if d.strip()]

        courses_raw = request.POST.get('courses', '')
        if courses_raw:
            settings_obj.courses = [c.strip() for c in courses_raw.splitlines() if c.strip()]

        academic_years_raw = request.POST.get('academic_years', '')
        if academic_years_raw:
            settings_obj.academic_years = [y.strip() for y in academic_years_raw.splitlines() if y.strip()]

        settings_obj.save()
        messages.success(request, 'Organization settings saved.')
        return redirect('org_detail', pk=org_pk)

    return render(request, 'organizations/org_settings.html', {
        'org': org,
        'settings_obj': settings_obj,
        'page_title': f'Settings — {org.name}',
    })


@login_required
def org_user_create(request, org_pk):
    _require_superadmin(request)
    org = get_object_or_404(Organization, pk=org_pk)
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
            return render(request, 'organizations/org_user_form.html', {
                'org': org, 'roles': roles, 'form_data': request.POST
            })

        user = User.objects.create_user(
            username=username, email=email,
            first_name=first_name, last_name=last_name,
        )
        user.set_password(password)
        user.is_active = is_active
        user.save()

        # Build profile and link organization
        profile = UserProfile.objects.create(user=user, phone=phone, organization=org)
        if role_id:
            try:
                role_obj = Role.objects.get(id=role_id)
                profile.role = role_obj
                group, _ = Group.objects.get_or_create(name=role_obj.name)
                group.user_set.add(user)
            except Role.DoesNotExist:
                pass
        profile.save()

        from authentication.views import log_action
        log_action(request.user, 'create', user, f'Created user {username} for organization {org.name}', request)
        messages.success(request, f"User '{username}' created successfully for {org.name}.")
        return redirect('org_detail', pk=org_pk)

    return render(request, 'organizations/org_user_form.html', {
        'org': org, 'roles': roles, 'page_title': f'Add User — {org.name}'
    })


@login_required
def org_subscription_pay(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.organization:
        return redirect('login')
        
    org = profile.organization
    sub = org.subscriptions.filter(is_active=False, payment_status='pending').first()
    
    if not sub:
        if org.subscriptions.filter(is_active=True, payment_status='active').exists():
            messages.info(request, 'Your subscription is already active!')
            return redirect('/')
        messages.error(request, 'No pending subscription found for your organization.')
        return redirect('logout')

    if request.method == 'POST':
        # Simulate payment verification
        sub.is_active = True
        sub.payment_status = 'active'
        sub.save()
        
        org.is_active = True
        org.save()
        
        messages.success(request, f'Payment successful! Your subscription for "{org.name}" is now active.')
        return redirect('/')

    return render(request, 'organizations/subscription_pay.html', {
        'org': org,
        'sub': sub,
        'no_sidebar': True,
        'page_title': 'Subscription Payment'
    })


