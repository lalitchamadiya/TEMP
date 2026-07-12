import shutil
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.contrib import messages

from .models import (
    StaffProfile, Visitor, InventoryItem,
    ComplaintTicket, SecurityGuard, IncidentReport,
    DutyAssignment
)
from student.models import Student
from room.models import HostelBuilding, HostelBlock, Floor, Room, Bed
from paybill.models import Payment, FeeStructure
from leave.models import HostelLeave
from django.contrib.auth.models import Group
from authentication.models import Role, UserProfile


# ──────────────────────────────────────────────────────
# Role-based access helper
# ──────────────────────────────────────────────────────
def _is_admin(user):
    if user.is_superuser:
        return True
    try:
        role = user.profile.role
        return role.is_superadmin or role.name in ('Admin', 'Staff')
    except Exception:
        return False


# ──────────────────────────────────────────────────────
# Root router
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login')
def dashboard(request):
    user = request.user
    role_name = None
    try:
        role_name = user.profile.role.name
    except Exception:
        pass

    if role_name == 'Student':
        return redirect('student_app:student_dashboard')
    if role_name == 'Warden':
        return redirect('warden_dashboard')
    return redirect('superadmin_dashboard')


# ──────────────────────────────────────────────────────
# SUPER ADMIN DASHBOARD
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login')
def superadmin_dashboard(request):
    if not _is_admin(request.user):
        return redirect('student_app:student_dashboard')

    today = timezone.now().date()
    now = timezone.now()

    # ── Students ──
    total_students = Student.objects.count()
    active_students = Student.objects.filter(status='Active').count()
    inactive_students = total_students - active_students
    gender_male = Student.objects.filter(gender='Male').count()
    gender_female = Student.objects.filter(gender='Female').count()

    # ── Rooms & Beds ──
    total_rooms = Room.objects.count()
    total_beds = Bed.objects.count()
    occupied_beds = Bed.objects.filter(student__isnull=False).count()
    vacant_beds = total_beds - occupied_beds
    occupancy_pct = round((occupied_beds / total_beds * 100) if total_beds else 0)
    total_blocks = HostelBlock.objects.count()
    total_floors = Floor.objects.count()

    # ── Financials ──
    today_revenue = Payment.objects.filter(
        transaction_status='SUCCESSFUL', created_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or 0

    month_start = today.replace(day=1)
    monthly_revenue = Payment.objects.filter(
        transaction_status='SUCCESSFUL', created_at__date__gte=month_start
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_revenue = Payment.objects.filter(
        transaction_status='SUCCESSFUL'
    ).aggregate(total=Sum('amount'))['total'] or 0

    pending_payments = Payment.objects.filter(transaction_status='PENDING').count()

    # Total expected (beds total_amount)
    total_expected = Bed.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    total_paid = Bed.objects.aggregate(total=Sum('paid_amount'))['total'] or 0
    total_outstanding = total_expected - total_paid

    # ── Leaves ──
    pending_leaves = HostelLeave.objects.filter(status='pending').count()
    approved_leaves_today = HostelLeave.objects.filter(status='approved', leave_date=today).count()

    # ── HMS Models ──
    total_staff = StaffProfile.objects.count()
    active_staff = StaffProfile.objects.filter(status='active').count()
    total_visitors_today = Visitor.objects.filter(visit_date=today).count()
    pending_visitors = Visitor.objects.filter(status='pending').count()
    open_complaints = ComplaintTicket.objects.filter(status__in=['pending', 'assigned', 'in_progress']).count()
    resolved_complaints = ComplaintTicket.objects.filter(status='resolved').count()
    total_guards = SecurityGuard.objects.filter(status='active').count()
    recent_incidents = IncidentReport.objects.order_by('-date')[:5]
    low_stock_items = InventoryItem.objects.filter(status='oos').count()
    damaged_items = InventoryItem.objects.filter(status='damaged').count()

    # ── Users & Roles ──
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()

    # ── System Health ──
    disk = shutil.disk_usage('/')
    disk_total_gb = round(disk.total / (1024 ** 3), 1)
    disk_used_gb = round(disk.used / (1024 ** 3), 1)
    disk_pct = round(disk.used / disk.total * 100, 1)

    # ── Chart Data ──
    # Monthly revenue last 6 months
    from datetime import timedelta
    monthly_labels = []
    monthly_data = []
    for i in range(5, -1, -1):
        d = (today.replace(day=1) - timedelta(days=1) * (i * 30)).replace(day=1)
        label = d.strftime('%b %Y')
        amt = Payment.objects.filter(
            transaction_status='SUCCESSFUL',
            created_at__year=d.year, created_at__month=d.month
        ).aggregate(t=Sum('amount'))['t'] or 0
        monthly_labels.append(label)
        monthly_data.append(float(amt))

    # Recent payments
    recent_payments = Payment.objects.filter(
        transaction_status='SUCCESSFUL'
    ).order_by('-created_at')[:8]

    # Recent complaints
    recent_complaints = ComplaintTicket.objects.order_by('-created_at')[:6]

    # Recent visitors
    recent_visitors = Visitor.objects.order_by('-visit_date', '-id')[:6]

    context = {
        'page_title': 'Super Admin Dashboard',
        # Students
        'total_students': total_students,
        'active_students': active_students,
        'inactive_students': inactive_students,
        'gender_male': gender_male,
        'gender_female': gender_female,
        # Rooms
        'total_blocks': total_blocks,
        'total_floors': total_floors,
        'total_rooms': total_rooms,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'vacant_beds': vacant_beds,
        'occupancy_pct': occupancy_pct,
        # Financials
        'today_revenue': today_revenue,
        'monthly_revenue': monthly_revenue,
        'total_revenue': total_revenue,
        'pending_payments': pending_payments,
        'total_outstanding': total_outstanding,
        # Leaves
        'pending_leaves': pending_leaves,
        'approved_leaves_today': approved_leaves_today,
        # HMS
        'total_staff': total_staff,
        'active_staff': active_staff,
        'total_visitors_today': total_visitors_today,
        'pending_visitors': pending_visitors,
        'open_complaints': open_complaints,
        'resolved_complaints': resolved_complaints,
        'total_guards': total_guards,
        'recent_incidents': recent_incidents,
        'low_stock_items': low_stock_items,
        'damaged_items': damaged_items,
        # Users
        'total_users': total_users,
        'active_users': active_users,
        # System
        'disk_total_gb': disk_total_gb,
        'disk_used_gb': disk_used_gb,
        'disk_pct': disk_pct,
        # Charts
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
        # Recent data
        'recent_payments': recent_payments,
        'recent_complaints': recent_complaints,
        'recent_visitors': recent_visitors,
    }
    return render(request, 'hms/superadmin_dashboard.html', context)


# ──────────────────────────────────────────────────────
# STAFF MANAGEMENT
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login')
def staff_list(request):
    if not _is_admin(request.user):
        return redirect('dashboard')

    from django.core.paginator import Paginator

    qs = StaffProfile.objects.select_related('user', 'user__profile').order_by('-id')

    # ── Filters ──
    search = request.GET.get('q', '').strip()
    designation_filter = request.GET.get('designation', '')
    status_filter = request.GET.get('status', '')
    shift_filter = request.GET.get('shift', '')
    performance_filter = request.GET.get('performance', '')

    if search:
        qs = qs.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(designation__icontains=search)
        )
    if designation_filter:
        qs = qs.filter(designation=designation_filter)
    if status_filter:
        qs = qs.filter(status=status_filter)
    if shift_filter:
        qs = qs.filter(shift=shift_filter)
    if performance_filter:
        qs = qs.filter(performance=performance_filter)

    # ── Bulk Actions ──
    if request.method == 'POST':
        action = request.POST.get('bulk_action')
        selected_ids = request.POST.getlist('selected_staff')
        if selected_ids and action:
            selected = StaffProfile.objects.filter(id__in=selected_ids)
            if action == 'activate':
                selected.update(status='active')
                if hasattr(selected.first(), 'user') and selected.first().user:
                    for s in selected:
                        if s.user:
                            s.user.is_active = True
                            s.user.save()
                messages.success(request, f'Activated {len(selected_ids)} staff member(s).')
            elif action == 'deactivate':
                selected.update(status='inactive')
                for s in selected:
                    if s.user:
                        s.user.is_active = False
                        s.user.save()
                messages.success(request, f'Deactivated {len(selected_ids)} staff member(s).')
            elif action == 'delete':
                for s in selected:
                    if s.user:
                        s.user.delete()
                    s.delete()
                messages.success(request, 'Selected staff members deleted.')
            elif action == 'export':
                import csv
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="staff_export.csv"'
                writer = csv.writer(response)
                writer.writerow(['Name', 'Email', 'Phone', 'Designation', 'Shift', 'Status', 'Performance', 'Salary', 'Date of Joining'])
                for s in selected:
                    writer.writerow([s.name, s.email, s.phone, s.get_designation_display(), s.get_shift_display(), s.get_status_display(), s.get_performance_display(), s.salary, s.doj])
                return response
        qs_str = request.META.get('QUERY_STRING', '')
        return redirect(request.path + ('?' + qs_str if qs_str else ''))

    # ── Pagination ──
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # ── Stats ──
    today = timezone.now().date()
    seven_days_ago = today - timezone.timedelta(days=7)
    stats = {
        'total': StaffProfile.objects.count(),
        'active': StaffProfile.objects.filter(status='active').count(),
        'inactive': StaffProfile.objects.filter(status='inactive').count(),
        'on_leave': StaffProfile.objects.filter(status='on_leave').count(),
        'new_this_week': StaffProfile.objects.filter(doj__gte=seven_days_ago).count(),
        'designations': StaffProfile.objects.values('designation').distinct().count(),
    }

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'search': search,
        'designation_filter': designation_filter,
        'status_filter': status_filter,
        'shift_filter': shift_filter,
        'performance_filter': performance_filter,
        'designations': StaffProfile.DESIGNATION_CHOICES,
        'shifts': StaffProfile.SHIFT_CHOICES,
        'statuses': StaffProfile.STATUS_CHOICES,
        'performances': StaffProfile.PERFORMANCE_CHOICES,
        'page_title': 'Staff Management',
    }
    return render(request, 'hms/staff_list.html', context)


@login_required(login_url='/authentication/login')
def staff_create(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    
    roles = Role.objects.filter(is_active=True)
    
    if request.method == 'POST':
        data = request.POST
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        designation = data.get('designation', '')
        salary = data.get('salary', 0) or 0
        shift = data.get('shift', 'morning')
        status = data.get('status', 'active')
        performance = data.get('performance', 'good')
        doj = data.get('doj') or timezone.now().date()
        documents = data.get('documents', '')

        # User credentials params
        username = data.get('username', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        role_id = data.get('role')
        
        errors = []
        if not name:
            errors.append('Name is required.')
        if not email:
            errors.append('Email is required.')
            
        if username:
            if User.objects.filter(username=username).exists():
                errors.append('Username already exists.')
            if User.objects.filter(email=email).exists():
                errors.append('Email already in use.')
            if password != confirm_password:
                errors.append('Passwords do not match.')
            if len(password) < 6:
                errors.append('Password must be at least 6 characters.')
        
        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'hms/staff_form.html', {
                'page_title': 'Add Staff Member',
                'designations': StaffProfile.DESIGNATION_CHOICES,
                'shifts': StaffProfile.SHIFT_CHOICES,
                'statuses': StaffProfile.STATUS_CHOICES,
                'performances': StaffProfile.PERFORMANCE_CHOICES,
                'roles': roles,
                'form_data': data
            })
            
        try:
            user = None
            if username:
                parts = name.split(' ', 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ''
                
                user = User.objects.create_user(
                    username=username, email=email,
                    first_name=first_name, last_name=last_name,
                    password=password
                )
                user.is_active = (status == 'active')
                user.save()
                
                # Create profile
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
                
            StaffProfile.objects.create(
                user=user,
                name=name,
                email=email,
                phone=phone,
                designation=designation,
                salary=salary,
                shift=shift,
                status=status,
                performance=performance,
                doj=doj,
                documents=documents,
            )
            messages.success(request, 'Staff member added successfully.')
            return redirect('staff_list')
        except Exception as e:
            messages.error(request, f'Error: {e}')
            return redirect('staff_list')

    return render(request, 'hms/staff_form.html', {
        'page_title': 'Add Staff Member',
        'designations': StaffProfile.DESIGNATION_CHOICES,
        'shifts': StaffProfile.SHIFT_CHOICES,
        'statuses': StaffProfile.STATUS_CHOICES,
        'performances': StaffProfile.PERFORMANCE_CHOICES,
        'roles': roles,
    })


@login_required(login_url='/authentication/login')
def staff_edit(request, pk):
    if not _is_admin(request.user):
        return redirect('dashboard')
    staff = get_object_or_404(StaffProfile, pk=pk)
    roles = Role.objects.filter(is_active=True)
    
    if request.method == 'POST':
        data = request.POST
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        designation = data.get('designation', staff.designation)
        salary = data.get('salary', 0) or 0
        shift = data.get('shift', 'morning')
        status = data.get('status', 'active')
        performance = data.get('performance', 'good')
        documents = data.get('documents', '')

        # User credentials params
        username = data.get('username', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        role_id = data.get('role')
        
        errors = []
        if staff.user:
            if User.objects.filter(email=email).exclude(id=staff.user.id).exists():
                errors.append('Email is already in use by another user.')
            if password:
                if password != confirm_password:
                    errors.append('Passwords do not match.')
                if len(password) < 6:
                    errors.append('Password must be at least 6 characters.')
        elif username:
            if User.objects.filter(username=username).exists():
                errors.append('Username already exists.')
            if User.objects.filter(email=email).exists():
                errors.append('Email already in use.')
            if password != confirm_password:
                errors.append('Passwords do not match.')
            if len(password) < 6:
                errors.append('Password must be at least 6 characters.')

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'hms/staff_form.html', {
                'page_title': 'Edit Staff Member',
                'staff': staff,
                'designations': StaffProfile.DESIGNATION_CHOICES,
                'shifts': StaffProfile.SHIFT_CHOICES,
                'statuses': StaffProfile.STATUS_CHOICES,
                'performances': StaffProfile.PERFORMANCE_CHOICES,
                'roles': roles,
                'form_data': data
            })

        try:
            if staff.user:
                user = staff.user
                parts = name.split(' ', 1)
                user.first_name = parts[0]
                user.last_name = parts[1] if len(parts) > 1 else ''
                user.email = email
                user.is_active = (status == 'active')
                if password:
                    user.set_password(password)
                user.save()
                
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.phone = phone
                if role_id:
                    try:
                        role_obj = Role.objects.get(id=role_id)
                        if profile.role and profile.role != role_obj:
                            old_group = Group.objects.filter(name=profile.role.name).first()
                            if old_group:
                                old_group.user_set.remove(user)
                        profile.role = role_obj
                        group, _ = Group.objects.get_or_create(name=role_obj.name)
                        group.user_set.add(user)
                    except Role.DoesNotExist:
                        pass
                if request.FILES.get('photo'):
                    profile.photo = request.FILES['photo']
                profile.save()
            elif username:
                parts = name.split(' ', 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ''
                
                user = User.objects.create_user(
                    username=username, email=email,
                    first_name=first_name, last_name=last_name,
                    password=password
                )
                user.is_active = (status == 'active')
                user.save()
                
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
                staff.user = user

            staff.name = name
            staff.email = email
            staff.phone = phone
            staff.designation = designation
            staff.salary = salary
            staff.shift = shift
            staff.status = status
            staff.performance = performance
            staff.documents = documents
            staff.save()
            messages.success(request, 'Staff member updated.')
            return redirect('staff_list')
        except Exception as e:
            messages.error(request, f'Error: {e}')
            return redirect('staff_list')

    return render(request, 'hms/staff_form.html', {
        'page_title': 'Edit Staff Member',
        'staff': staff,
        'designations': StaffProfile.DESIGNATION_CHOICES,
        'shifts': StaffProfile.SHIFT_CHOICES,
        'statuses': StaffProfile.STATUS_CHOICES,
        'performances': StaffProfile.PERFORMANCE_CHOICES,
        'roles': roles,
    })


@login_required(login_url='/authentication/login')
def staff_delete(request, pk):
    if not _is_admin(request.user):
        return redirect('dashboard')
    staff = get_object_or_404(StaffProfile, pk=pk)
    if request.method == 'POST':
        if staff.user:
            staff.user.delete()
        staff.delete()
        messages.success(request, 'Staff member removed.')
    return redirect('staff_list')


@login_required(login_url='/authentication/login')
def staff_toggle_status(request, pk):
    """Toggle a staff member's status between active and inactive."""
    if not _is_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        staff = get_object_or_404(StaffProfile, pk=pk)
        if staff.status == 'active':
            staff.status = 'inactive'
            if staff.user:
                staff.user.is_active = False
                staff.user.save()
            messages.success(request, f'{staff.name} set to Inactive.')
        else:
            staff.status = 'active'
            if staff.user:
                staff.user.is_active = True
                staff.user.save()
            messages.success(request, f'{staff.name} set to Active.')
        staff.save()
    return redirect('staff_list')


# ──────────────────────────────────────────────────────
# VISITOR MANAGEMENT
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login')
def visitor_list(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    visitors = Visitor.objects.select_related('student').order_by('-visit_date', '-id')
    query = request.GET.get('q', '')
    if query:
        visitors = visitors.filter(Q(name__icontains=query) | Q(student__name__icontains=query))
    context = {'visitors': visitors, 'query': query, 'page_title': 'Visitor Management'}
    return render(request, 'hms/visitor_list.html', context)


@login_required(login_url='/authentication/login')
def visitor_create(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    students = Student.objects.filter(status='Active').order_by('name')
    if request.method == 'POST':
        data = request.POST
        student = get_object_or_404(Student, pk=data['student_id'])
        Visitor.objects.create(
            name=data['name'],
            phone=data['phone'],
            student=student,
            relation=data['relation'],
            visit_date=data.get('visit_date') or timezone.now().date(),
            purpose=data['purpose'],
            status='pending',
        )
        messages.success(request, 'Visitor registered successfully.')
        return redirect('visitor_list')
    return render(request, 'hms/visitor_form.html', {
        'page_title': 'Register Visitor',
        'students': students,
    })


@login_required(login_url='/authentication/login')
def visitor_update_status(request, pk, status):
    if not _is_admin(request.user):
        return redirect('dashboard')
    visitor = get_object_or_404(Visitor, pk=pk)
    if status in ['approved', 'denied', 'completed']:
        visitor.status = status
        if status == 'approved':
            visitor.entry_time = timezone.now().time()
        visitor.save()
        messages.success(request, f'Visitor status updated to {status}.')
    return redirect('visitor_list')


@login_required(login_url='/authentication/login')
def visitor_checkout(request, pk):
    if not _is_admin(request.user):
        return redirect('dashboard')
    visitor = get_object_or_404(Visitor, pk=pk)
    visitor.exit_time = timezone.now().time()
    visitor.status = 'completed'
    visitor.save()
    messages.success(request, 'Visitor checked out successfully.')
    return redirect('visitor_list')


# ──────────────────────────────────────────────────────
# INVENTORY MANAGEMENT
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login')
def inventory_list(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    items = InventoryItem.objects.all().order_by('-purchase_date')
    category = request.GET.get('category', '')
    if category:
        items = items.filter(category=category)
    context = {
        'items': items, 'category': category,
        'page_title': 'Inventory Management',
        'categories': InventoryItem.CATEGORY_CHOICES,
        'total_items': InventoryItem.objects.count(),
        'low_stock': InventoryItem.objects.filter(status='oos').count(),
        'damaged': InventoryItem.objects.filter(status='damaged').count(),
    }
    return render(request, 'hms/inventory_list.html', context)


@login_required(login_url='/authentication/login')
def inventory_create(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        data = request.POST
        InventoryItem.objects.create(
            name=data['name'],
            category=data['category'],
            quantity=int(data.get('quantity', 1)),
            available_quantity=int(data.get('available_quantity', 1)),
            vendor_name=data.get('vendor_name', ''),
            vendor_contact=data.get('vendor_contact', ''),
            status=data.get('status', 'good'),
            purchase_order_no=data.get('purchase_order_no', ''),
        )
        messages.success(request, 'Inventory item added.')
        return redirect('inventory_list')
    return render(request, 'hms/inventory_form.html', {
        'page_title': 'Add Inventory Item',
        'categories': InventoryItem.CATEGORY_CHOICES,
        'statuses': InventoryItem.STATUS_CHOICES,
    })


@login_required(login_url='/authentication/login')
def inventory_edit(request, pk):
    if not _is_admin(request.user):
        return redirect('dashboard')
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        data = request.POST
        item.name = data.get('name', item.name)
        item.category = data.get('category', item.category)
        item.quantity = int(data.get('quantity', item.quantity))
        item.available_quantity = int(data.get('available_quantity', item.available_quantity))
        item.vendor_name = data.get('vendor_name', item.vendor_name)
        item.vendor_contact = data.get('vendor_contact', item.vendor_contact)
        item.status = data.get('status', item.status)
        item.purchase_order_no = data.get('purchase_order_no', item.purchase_order_no)
        item.save()
        messages.success(request, 'Item updated.')
        return redirect('inventory_list')
    return render(request, 'hms/inventory_form.html', {
        'page_title': 'Edit Inventory Item',
        'item': item,
        'categories': InventoryItem.CATEGORY_CHOICES,
        'statuses': InventoryItem.STATUS_CHOICES,
    })


@login_required(login_url='/authentication/login')
def inventory_delete(request, pk):
    if not _is_admin(request.user):
        return redirect('dashboard')
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deleted.')
    return redirect('inventory_list')


# ──────────────────────────────────────────────────────
# COMPLAINT MANAGEMENT
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login')
def complaint_list(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    complaints = ComplaintTicket.objects.select_related('student', 'assigned_to').order_by('-created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    staff_members = StaffProfile.objects.filter(status='active')
    context = {
        'complaints': complaints,
        'status_filter': status_filter,
        'staff_members': staff_members,
        'page_title': 'Complaint Management',
        'statuses': ComplaintTicket.STATUS_CHOICES,
    }
    return render(request, 'hms/complaint_list.html', context)


@login_required(login_url='/authentication/login')
def complaint_assign(request, pk):
    if not _is_admin(request.user):
        return redirect('dashboard')
    complaint = get_object_or_404(ComplaintTicket, pk=pk)
    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        if staff_id:
            complaint.assigned_to = get_object_or_404(StaffProfile, pk=staff_id)
            complaint.status = 'assigned'
            complaint.save()
            messages.success(request, 'Complaint assigned.')
    return redirect('complaint_list')


@login_required(login_url='/authentication/login')
def complaint_resolve(request, pk):
    if not _is_admin(request.user):
        return redirect('dashboard')
    complaint = get_object_or_404(ComplaintTicket, pk=pk)
    if request.method == 'POST':
        complaint.status = 'resolved'
        complaint.resolved_at = timezone.now()
        complaint.feedback = request.POST.get('feedback', '')
        complaint.save()
        messages.success(request, 'Complaint resolved.')
    return redirect('complaint_list')


# ──────────────────────────────────────────────────────
# SECURITY MANAGEMENT
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login')
def security_list(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    guards = SecurityGuard.objects.all().order_by('-id')
    incidents = IncidentReport.objects.select_related('guard').order_by('-date', '-id')[:20]
    context = {
        'guards': guards,
        'incidents': incidents,
        'page_title': 'Security Management',
    }
    return render(request, 'hms/security_list.html', context)


@login_required(login_url='/authentication/login')
def security_guard_create(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        data = request.POST
        SecurityGuard.objects.create(
            name=data['name'],
            phone=data['phone'],
            gate_no=data.get('gate_no', 'Main Gate 1'),
            shift=data.get('shift', 'morning'),
            status=data.get('status', 'active'),
        )
        messages.success(request, 'Security guard added.')
    return redirect('security_list')


@login_required(login_url='/authentication/login')
def incident_report_create(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        data = request.POST
        guard_id = data.get('guard_id')
        guard = SecurityGuard.objects.filter(pk=guard_id).first() if guard_id else None
        IncidentReport.objects.create(
            title=data['title'],
            description=data['description'],
            guard=guard,
            severity=data.get('severity', 'low'),
            action_taken=data.get('action_taken', ''),
        )
        messages.success(request, 'Incident report filed.')
    return redirect('security_list')


# ──────────────────────────────────────────────────────
# HOSTEL LOGISTICS MANAGER
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login')
def hostel_manager(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    blocks = HostelBlock.objects.prefetch_related('floors__rooms__bed_set').all()
    all_beds = Bed.objects.select_related('room', 'student').all()
    context = {
        'blocks': blocks,
        'all_beds': all_beds,
        'total_rooms': Room.objects.count(),
        'total_beds': Bed.objects.count(),
        'occupied_beds': Bed.objects.filter(student__isnull=False).count(),
        'page_title': 'Hostel Infrastructure Manager',
    }
    return render(request, 'hms/hostel_manager.html', context)


@login_required(login_url='/authentication/login')
def hostel_block_create(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        HostelBlock.objects.get_or_create(
            name=request.POST['name'],
            defaults={'description': request.POST.get('description', '')}
        )
        messages.success(request, 'Block created.')
    return redirect('hostel_manager')


@login_required(login_url='/authentication/login')
def hostel_floor_create(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        block = get_object_or_404(HostelBlock, pk=request.POST['block_id'])
        Floor.objects.get_or_create(block=block, floor_number=int(request.POST['floor_number']))
        messages.success(request, 'Floor added.')
    return redirect('hostel_manager')


@login_required(login_url='/authentication/login')
def hostel_room_create(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        data = request.POST
        floor = get_object_or_404(Floor, pk=data['floor_id'])
        Room.objects.create(
            room_number=data['room_number'],
            room_type=data['room_type'],
            gender=data['gender'],
            floor=floor,
        )
        messages.success(request, 'Room added.')
    return redirect('hostel_manager')


@login_required(login_url='/authentication/login')
def hostel_bed_create(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        data = request.POST
        room = get_object_or_404(Room, pk=data['room_id'])
        Bed.objects.create(
            room=room,
            bed_number=data['bed_number'],
            total_amount=float(data.get('total_amount', 0)),
            remaining_amount=float(data.get('total_amount', 0)),
        )
        messages.success(request, 'Bed added.')
    return redirect('hostel_manager')


@login_required(login_url='/authentication/login')
def hostel_allocate_bed(request, pk):
    if not _is_admin(request.user):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
        return redirect('dashboard')
    bed = get_object_or_404(Bed, pk=pk)
    if request.method == 'POST':
        student = get_object_or_404(Student, pk=request.POST['student_id'])
        bed.student = student
        bed.save()
        msg = f'Bed allocated to {student.name}.'
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': msg})
        messages.success(request, msg)
    next_url = request.GET.get('next') or 'hostel_manager'
    return redirect(next_url)


@login_required(login_url='/authentication/login')
def hostel_deallocate_bed(request, pk):
    if not _is_admin(request.user):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
        return redirect('dashboard')
    bed = get_object_or_404(Bed, pk=pk)
    if request.method == 'POST':
        bed.student = None
        bed.save()
        msg = 'Bed deallocated.'
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': msg})
        messages.success(request, msg)
    next_url = request.GET.get('next') or 'hostel_manager'
    return redirect(next_url)


# ──────────────────────────────────────────────────────
# FEE MANAGEMENT
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login')
def fee_manager(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    fee_structures = FeeStructure.objects.all()
    recent_payments = Payment.objects.order_by('-created_at')[:15]
    today = timezone.now().date()
    context = {
        'fee_structures': fee_structures,
        'recent_payments': recent_payments,
        'today_revenue': Payment.objects.filter(
            transaction_status='SUCCESSFUL', created_at__date=today
        ).aggregate(t=Sum('amount'))['t'] or 0,
        'monthly_revenue': Payment.objects.filter(
            transaction_status='SUCCESSFUL',
            created_at__date__gte=today.replace(day=1)
        ).aggregate(t=Sum('amount'))['t'] or 0,
        'total_revenue': Payment.objects.filter(
            transaction_status='SUCCESSFUL'
        ).aggregate(t=Sum('amount'))['t'] or 0,
        'pending_count': Payment.objects.filter(transaction_status='PENDING').count(),
        'page_title': 'Fee & Financial Management',
        'fee_types': FeeStructure.FEE_TYPES,
    }
    return render(request, 'hms/fee_manager.html', context)


@login_required(login_url='/authentication/login')
def fee_structure_create(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        data = request.POST
        FeeStructure.objects.update_or_create(
            fee_type=data['fee_type'],
            defaults={
                'amount': float(data['amount']),
                'due_date': data.get('due_date') or None,
                'late_fee_per_day': float(data.get('late_fee_per_day', 0)),
            }
        )
        messages.success(request, 'Fee structure saved.')
    return redirect('fee_manager')


@login_required(login_url='/authentication/login')
def fee_payment_create(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        data = request.POST
        student = Student.objects.filter(pk=data.get('student_id')).first()
        Payment.objects.create(
            student=student,
            transaction_id=f'ADMIN-{timezone.now().timestamp():.0f}',
            enrollment_number=student.roll if student else data.get('enrollment_number', ''),
            user_name=student.name if student else data.get('user_name', ''),
            contact_no=student.phone_number if student else '',
            amount=float(data['amount']),
            payment_type=data.get('payment_type', 'Cash'),
            transaction_status='SUCCESSFUL',
        )
        messages.success(request, 'Payment recorded.')
    return redirect('fee_manager')


# ──────────────────────────────────────────────────────
# REPORTS & EXPORT
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login')
def reports_dashboard(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    context = {
        'page_title': 'Reports & Analytics',
        'total_students': Student.objects.count(),
        'total_payments': Payment.objects.filter(transaction_status='SUCCESSFUL').count(),
        'total_revenue': Payment.objects.filter(
            transaction_status='SUCCESSFUL'
        ).aggregate(t=Sum('amount'))['t'] or 0,
        'total_complaints': ComplaintTicket.objects.count(),
        'staff_count': StaffProfile.objects.count(),
    }
    return render(request, 'hms/reports.html', context)


@login_required(login_url='/authentication/login')
def export_report(request, module):
    if not _is_admin(request.user):
        return redirect('dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{module}_report.csv"'
    writer = csv.writer(response)

    if module == 'students':
        writer.writerow(['ID', 'Name', 'Email', 'Course', 'Department', 'Status', 'Admission Date'])
        for s in Student.objects.all():
            writer.writerow([s.student_id, s.name, s.email, s.course, s.department, s.status, s.admission_date])

    elif module == 'payments':
        writer.writerow(['Transaction ID', 'Student', 'Amount', 'Type', 'Status', 'Date'])
        for p in Payment.objects.all():
            writer.writerow([p.transaction_id, p.user_name, p.amount, p.payment_type, p.transaction_status, p.created_at.date()])

    elif module == 'staff':
        writer.writerow(['ID', 'Name', 'Email', 'Designation', 'Shift', 'Status', 'Salary'])
        for s in StaffProfile.objects.all():
            writer.writerow([s.id, s.name, s.email, s.get_designation_display(), s.shift, s.status, s.salary])

    elif module == 'complaints':
        writer.writerow(['ID', 'Title', 'Student', 'Category', 'Status', 'Created'])
        for c in ComplaintTicket.objects.select_related('student').all():
            writer.writerow([c.id, c.title, c.student.name, c.get_category_display(), c.status, c.created_at.date()])

    elif module == 'visitors':
        writer.writerow(['ID', 'Name', 'Phone', 'Student', 'Relation', 'Date', 'Status', 'Pass Code'])
        for v in Visitor.objects.select_related('student').all():
            writer.writerow([v.id, v.name, v.phone, v.student.name, v.relation, v.visit_date, v.status, v.pass_code])

    else:
        writer.writerow(['No data available for this module.'])

    return response


# ──────────────────────────────────────────────────────
# STAFF DUTY ASSIGNMENT MODULE
# ──────────────────────────────────────────────────────
from authentication.decorators import permission_required, api_permission_required

@login_required(login_url='/authentication/login')
@permission_required('duty_management', 'view')
def duty_list(request):
    assignments = DutyAssignment.objects.select_related('staff', 'building', 'block', 'floor').filter(is_active=True).order_by('-assigned_date')
    staff_members = StaffProfile.objects.filter(status='active').order_by('name')
    buildings = HostelBuilding.objects.filter(is_active=True).order_by('name')
    blocks = HostelBlock.objects.all().order_by('name')
    
    # We will pass the list of assignments, active staff, buildings, blocks
    context = {
        'page_title': 'Staff Duty Assignments',
        'assignments': assignments,
        'staff_members': staff_members,
        'buildings': buildings,
        'blocks': blocks,
    }
    return render(request, 'hms/duty_list.html', context)


@login_required(login_url='/authentication/login')
@permission_required('duty_management', 'add')
def duty_assign(request):
    if request.method == 'POST':
        data = request.POST
        staff_id = data.get('staff_id')
        duty_title = data.get('duty_title', '').strip()
        building_id = data.get('building_id')
        block_id = data.get('block_id')
        floor_id = data.get('floor_id')
        specific_location = data.get('specific_location', '').strip()
        shift_start = data.get('shift_start') or None
        shift_end = data.get('shift_end') or None
        description = data.get('description', '').strip()
        
        staff = get_object_or_404(StaffProfile, pk=staff_id)
        building = HostelBuilding.objects.filter(pk=building_id).first() if building_id else None
        block = HostelBlock.objects.filter(pk=block_id).first() if block_id else None
        floor = Floor.objects.filter(pk=floor_id).first() if floor_id else None
        
        DutyAssignment.objects.create(
            staff=staff,
            duty_title=duty_title,
            building=building,
            block=block,
            floor=floor,
            specific_location=specific_location,
            shift_start=shift_start,
            shift_end=shift_end,
            description=description
        )
        messages.success(request, f'Duty assigned to {staff.name} successfully.')
    return redirect('duty_list')


@login_required(login_url='/authentication/login')
@permission_required('duty_management', 'edit')
def duty_edit(request, pk):
    assignment = get_object_or_404(DutyAssignment, pk=pk)
    if request.method == 'POST':
        data = request.POST
        staff_id = data.get('staff_id')
        duty_title = data.get('duty_title', '').strip()
        building_id = data.get('building_id')
        block_id = data.get('block_id')
        floor_id = data.get('floor_id')
        specific_location = data.get('specific_location', '').strip()
        shift_start = data.get('shift_start') or None
        shift_end = data.get('shift_end') or None
        description = data.get('description', '').strip()
        
        staff = get_object_or_404(StaffProfile, pk=staff_id)
        building = HostelBuilding.objects.filter(pk=building_id).first() if building_id else None
        block = HostelBlock.objects.filter(pk=block_id).first() if block_id else None
        floor = Floor.objects.filter(pk=floor_id).first() if floor_id else None
        
        assignment.staff = staff
        assignment.duty_title = duty_title
        assignment.building = building
        assignment.block = block
        assignment.floor = floor
        assignment.specific_location = specific_location
        assignment.shift_start = shift_start
        assignment.shift_end = shift_end
        assignment.description = description
        assignment.save()
        messages.success(request, f"Duty assignment for {staff.name} updated.")
    return redirect('duty_list')


@login_required(login_url='/authentication/login')
@permission_required('duty_management', 'delete')
def duty_delete(request, pk):
    assignment = get_object_or_404(DutyAssignment, pk=pk)
    if request.method == 'POST':
        assignment.delete()
        messages.success(request, 'Duty assignment deleted.')
    return redirect('duty_list')


@login_required(login_url='/authentication/login')
@api_permission_required('duty_management', 'view')
def get_floors_for_building(request):
    building_id = request.GET.get('building_id')
    if not building_id:
        return JsonResponse({'floors': []})
    floors = Floor.objects.filter(building_id=building_id).order_by('floor_number')
    data = [{'id': f.id, 'floor_number': f.floor_number} for f in floors]
    return JsonResponse({'floors': data})


# ──────────────────────────────────────────────────────
# MULTI-HOSTEL CONTROL CENTER
# ──────────────────────────────────────────────────────
from authentication.models import Hostel

def _is_super_admin(user):
    if user.is_superuser:
        return True
    try:
        return user.profile.role.is_superadmin or user.profile.role.name == 'Super Admin'
    except Exception:
        return False

@login_required(login_url='/authentication/login')
def superadmin_control_center(request):
    if not _is_super_admin(request.user):
        return redirect('dashboard')
    
    # Combined Metrics
    total_hostels = Hostel.objects.count()
    active_hostels_count = Hostel.objects.filter(is_active=True).count()
    
    total_beds = Bed.objects.count()
    occupied_beds = Bed.objects.filter(student__isnull=False).count()
    vacant_beds = total_beds - occupied_beds
    combined_occupancy = round((occupied_beds / total_beds * 100) if total_beds else 0)
    
    total_revenue = Payment.objects.filter(transaction_status='SUCCESSFUL').aggregate(total=Sum('amount'))['total'] or 0
    total_students = Student.objects.count()
    total_staff = StaffProfile.objects.count()
    open_complaints = ComplaintTicket.objects.filter(status__in=['pending', 'assigned', 'in_progress']).count()

    # Hostel-wise Stats
    hostels = Hostel.objects.all().order_by('name')
    hostels_data = []
    for h in hostels:
        # Beds occupied vs total
        h_beds = Bed.objects.filter(room__hostel=h)
        h_total_beds = h_beds.count()
        h_occupied_beds = h_beds.filter(student__isnull=False).count()
        h_vacant_beds = h_total_beds - h_occupied_beds
        h_occupancy_pct = round((h_occupied_beds / h_total_beds * 100) if h_total_beds else 0)
        
        h_students = Student.objects.filter(hostel=h).count()
        h_staff = StaffProfile.objects.filter(hostel=h).count()
        
        h_revenue = Payment.objects.filter(
            Q(hostel=h) | Q(student__hostel=h),
            transaction_status='SUCCESSFUL'
        ).distinct().aggregate(total=Sum('amount'))['total'] or 0
        
        h_complaints = ComplaintTicket.objects.filter(
            student__hostel=h,
            status__in=['pending', 'assigned', 'in_progress']
        ).count()
        
        hostels_data.append({
            'hostel': h,
            'total_beds': h_total_beds,
            'occupied_beds': h_occupied_beds,
            'vacant_beds': h_vacant_beds,
            'occupancy_pct': h_occupancy_pct,
            'students_count': h_students,
            'staff_count': h_staff,
            'revenue': h_revenue,
            'open_complaints': h_complaints,
        })
        
    students = Student.objects.all().order_by('name')
    staff_members = StaffProfile.objects.all().order_by('name')
    
    context = {
        'page_title': 'Multi-Hostel Control Center',
        'total_hostels': total_hostels,
        'active_hostels_count': active_hostels_count,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'vacant_beds': vacant_beds,
        'combined_occupancy': combined_occupancy,
        'total_revenue': total_revenue,
        'total_students': total_students,
        'total_staff': total_staff,
        'open_complaints': open_complaints,
        'hostels_data': hostels_data,
        'students': students,
        'staff_members': staff_members,
        'hostels': hostels,
    }
    return render(request, 'hms/superadmin_control_center.html', context)


@login_required(login_url='/authentication/login')
def hostel_toggle_status_ajax(request, pk):
    if not _is_super_admin(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    if request.method == 'POST':
        hostel = get_object_or_404(Hostel, pk=pk)
        
        # Do not allow deactivating if it's the last active hostel
        active_count = Hostel.objects.filter(is_active=True).count()
        if hostel.is_active and active_count <= 1:
            return JsonResponse({
                'success': False,
                'error': 'Cannot deactivate the only active hostel in the system.'
            }, status=400)
            
        hostel.is_active = not hostel.is_active
        hostel.save()
        return JsonResponse({
            'success': True,
            'is_active': hostel.is_active
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required(login_url='/authentication/login')
def transfer_student(request):
    if not _is_super_admin(request.user):
         return redirect('dashboard')
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        target_hostel_id = request.POST.get('target_hostel_id')
        
        student = get_object_or_404(Student, pk=student_id)
        target_hostel = get_object_or_404(Hostel, pk=target_hostel_id)
        
        if student.hostel == target_hostel:
            messages.warning(request, f"{student.name} is already in {target_hostel.name}.")
            return redirect('superadmin_control_center')
            
        # Deallocate current bed assignment
        Bed.objects.filter(student=student).update(
            student=None,
            paid_amount=0,
            remaining_amount=0,
            total_amount=0
        )
        
        # Move student to new hostel partition
        student.hostel = target_hostel
        student.save()
        
        messages.success(request, f"Successfully transferred Student {student.name} to {target_hostel.name}.")
    return redirect('superadmin_control_center')


@login_required(login_url='/authentication/login')
def transfer_staff(request):
    if not _is_super_admin(request.user):
         return redirect('dashboard')
    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        target_hostel_id = request.POST.get('target_hostel_id')
        
        staff = get_object_or_404(StaffProfile, pk=staff_id)
        target_hostel = get_object_or_404(Hostel, pk=target_hostel_id)
        
        if staff.hostel == target_hostel:
            messages.warning(request, f"{staff.name} is already assigned to {target_hostel.name}.")
            return redirect('superadmin_control_center')
            
        # Move staff member to new hostel partition
        staff.hostel = target_hostel
        staff.save()
        
        messages.success(request, f"Successfully transferred Staff {staff.name} to {target_hostel.name}.")
    return redirect('superadmin_control_center')


@login_required(login_url='/authentication/login')
def cross_hostel_report_csv(request):
    if not _is_super_admin(request.user):
         return redirect('dashboard')
         
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cross_hostel_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Hostel Name', 'Hostel Code', 'Type', 'Status', 'Capacity (Beds)', 
        'Occupied Beds', 'Vacant Beds', 'Occupancy (%)', 'Total Students', 
        'Active Staff', 'Collected Revenue', 'Open Complaints'
    ])
    
    hostels = Hostel.objects.all().order_by('name')
    for h in hostels:
        h_beds = Bed.objects.filter(room__hostel=h)
        h_total_beds = h_beds.count()
        h_occupied_beds = h_beds.filter(student__isnull=False).count()
        h_vacant_beds = h_total_beds - h_occupied_beds
        h_occupancy_pct = round((h_occupied_beds / h_total_beds * 100) if h_total_beds else 0)
        
        h_students = Student.objects.filter(hostel=h).count()
        h_staff = StaffProfile.objects.filter(hostel=h).count()
        
        h_revenue = Payment.objects.filter(
            Q(hostel=h) | Q(student__hostel=h),
            transaction_status='SUCCESSFUL'
        ).distinct().aggregate(total=Sum('amount'))['total'] or 0
        
        h_complaints = ComplaintTicket.objects.filter(
            student__hostel=h,
            status__in=['pending', 'assigned', 'in_progress']
        ).count()
        
        writer.writerow([
            h.name, h.code, h.hostel_type, 
            'Active' if h.is_active else 'Inactive',
            h_total_beds, h_occupied_beds, h_vacant_beds, 
            h_occupancy_pct, h_students, h_staff, h_revenue, h_complaints
        ])
        
    return response