from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from authentication.decorators import role_required, permission_required
from django.core.exceptions import PermissionDenied
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.db import transaction, models
from .models import HostelLeave, GatePass
from student.models import Student, Attendance
from authentication.models import Notification, AuditLog
import uuid

def generate_gate_pass_no():
    return f"GP-{uuid.uuid4().hex[:8].upper()}"

@login_required(login_url='/authentication/login')
@permission_required('leave', 'view')
def leave_base(request):
    if hasattr(request.user, 'profile') and request.user.profile.role.name == 'Student':
        pending_leave_count = HostelLeave.objects.filter(student__user=request.user, status='pending').count()
    else:
        pending_leave_count = HostelLeave.objects.filter(status='pending').count()
    return render(request, 'leave/leave_base.html', {'leave': pending_leave_count})

@login_required(login_url='/authentication/login')
@permission_required('leave', 'edit')
def edit_leave(request, leave_id):
    leave = get_object_or_404(HostelLeave, id=leave_id)
    if hasattr(request.user, 'profile') and request.user.profile.role.name == 'Student':
        if leave.student.user != request.user:
            raise PermissionDenied
            
    student = leave.student
    if request.method == 'POST':
        leave.reason = request.POST.get('reason')
        leave.leave_date = request.POST.get('leave_date')
        leave.return_date = request.POST.get('return_date')
        leave.start_time = request.POST.get('start_time')
        leave.end_time = request.POST.get('end_time')
        leave.destination = request.POST.get('destination')
        leave.transport_mode = request.POST.get('transport_mode')
        leave.remarks = request.POST.get('remarks')
        try:
            leave.save()
            messages.success(request, 'Leave request updated successfully.')
            return redirect('leave_record')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    context = {'leave': leave, 'student_details': student}
    return render(request, 'leave/edit_leave.html', context)

def process_leave_action(request, leave, action):
    if action == 'approve':
        with transaction.atomic():
            leave.status = 'approved'
            leave.approved_by = request.user
            leave.approval_date = timezone.now()
            
            # Calculate total days
            if leave.return_date and leave.leave_date:
                leave.total_days = (leave.return_date - leave.leave_date).days or 1
            leave.save()

            # Generate Gate Pass
            gp_no = generate_gate_pass_no()
            GatePass.objects.create(gate_pass_no=gp_no, leave_request=leave)

            # Update Student Status
            student = leave.student
            student.status = 'On Leave'
            student.save()

            # Mark Attendance as 'On Leave' for the dates
            current_date = leave.leave_date
            end_date = leave.return_date or leave.leave_date
            while current_date <= end_date:
                Attendance.objects.update_or_create(
                    student=student,
                    date=current_date,
                    defaults={'status': 'On Leave', 'marked_by': request.user}
                )
                current_date += timedelta(days=1)

            # Create Notification
            Notification.objects.create(
                user=student.user,
                message=f"Your leave request for {leave.leave_date} has been approved. Gate Pass {gp_no} generated."
            )

            # Log to AuditLog
            AuditLog.objects.create(
                actor=request.user,
                target_user=student.user,
                action='gate_pass',
                details=f"Approved leave and generated Gate Pass {gp_no} for student {student.name}",
                ip_address=request.META.get('REMOTE_ADDR')
            )

    elif action == 'reject':
        leave.status = 'rejected'
        leave.save()
        Notification.objects.create(
            user=leave.student.user,
            message=f"Your leave request for {leave.leave_date} has been rejected."
        )

    elif action == 'entered':
        with transaction.atomic():
            leave.status = 'entered'
            leave.save()
            
            # Restore Student Status
            student = leave.student
            student.status = 'Active'
            student.save()
            
            # Log return
            AuditLog.objects.create(
                actor=request.user,
                target_user=student.user,
                action='edit',
                details=f"Student {student.name} marked as returned from leave.",
                ip_address=request.META.get('REMOTE_ADDR')
            )

@login_required(login_url='/authentication/login')
@permission_required('leave', 'view')
def leave_record(request):
    if request.method == 'POST':
        # Action requires approve/reject permission
        action = request.POST.get('action')
        # Check permissions safely (Superusers and active super-admins always bypass)
        is_authorized = False
        if request.user.is_superuser:
            is_authorized = True
        elif hasattr(request.user, 'profile') and request.user.profile.role:
            role = request.user.profile.role
            if role.is_superadmin:
                is_authorized = True
            else:
                perm = role.permissions.filter(module__code='leave').first()
                if perm:
                    if action == 'approve' and getattr(perm, 'can_approve', False):
                        is_authorized = True
                    elif action == 'reject' and getattr(perm, 'can_reject', False):
                        is_authorized = True

        if not is_authorized:
            raise PermissionDenied

        leave_id = request.POST.get('leave_id')
        try:
            leave = HostelLeave.objects.get(id=leave_id)
            process_leave_action(request, leave, action)
            messages.success(request, f"Status updated to {leave.status}.")
        except HostelLeave.DoesNotExist:
            messages.error(request, "Leave request not found.")

    if hasattr(request.user, 'profile') and request.user.profile.role.name == 'Student':
        leave_requests = HostelLeave.objects.filter(student__user=request.user, status__in=['rejected', 'entered'])
    else:
        leave_requests = HostelLeave.objects.filter(status__in=['rejected', 'entered'])
    return render(request, 'leave/leave_record.html', {'leave_requests': leave_requests})

@login_required(login_url='/authentication/login')
@permission_required('leave', 'view')
def pending_leave(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        # Check permissions safely (Superusers and active super-admins always bypass)
        is_authorized = False
        if request.user.is_superuser:
            is_authorized = True
        elif hasattr(request.user, 'profile') and request.user.profile.role:
            role = request.user.profile.role
            if role.is_superadmin:
                is_authorized = True
            else:
                perm = role.permissions.filter(module__code='leave').first()
                if perm:
                    if action == 'approve' and getattr(perm, 'can_approve', False):
                        is_authorized = True
                    elif action == 'reject' and getattr(perm, 'can_reject', False):
                        is_authorized = True

        if not is_authorized:
            raise PermissionDenied

        leave_id = request.POST.get('leave_id')
        try:
            leave = HostelLeave.objects.get(id=leave_id)
            process_leave_action(request, leave, action)
            messages.success(request, "Status updated.")
        except HostelLeave.DoesNotExist:
            messages.error(request, "Not found.")
        return redirect('pending_leave')

    if hasattr(request.user, 'profile') and request.user.profile.role.name == 'Student':
        pending_leave_requests = HostelLeave.objects.filter(student__user=request.user, status__in=['pending', 'approved'])
    else:
        pending_leave_requests = HostelLeave.objects.filter(status__in=['pending', 'approved'])
    return render(request, 'leave/pending_leave.html', {'pending_leave_requests': pending_leave_requests})

@login_required(login_url='/authentication/login')
@permission_required('leave', 'add')
def add_leave(request):
    if request.method == 'POST':
        enrollment_number = request.POST.get('enrollment_number')
        reason = request.POST.get('reason')
        leave_date_str = request.POST.get('leave_date')
        return_date_str = request.POST.get('return_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        destination = request.POST.get('destination')
        transport_mode = request.POST.get('transport_mode')
        remarks = request.POST.get('remarks')

        try:
            student = Student.objects.get(roll=enrollment_number)
            # Isolation check for Student role
            if hasattr(request.user, 'profile') and request.user.profile.role.name == 'Student':
                if student.user != request.user:
                    raise PermissionDenied("You can only add leave for yourself.")

            if HostelLeave.objects.filter(student=student).exclude(status__in=['entered', 'rejected']).exists():
                messages.error(request, 'Active or pending request already exists.')
                return redirect('add_leave') 

            leave_date = datetime.strptime(leave_date_str, '%Y-%m-%d').date()
            return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date() if return_date_str else None
            
            HostelLeave.objects.create(
                student=student, 
                leave_date=leave_date, 
                return_date=return_date,
                start_time=start_time,
                end_time=end_time,
                reason=reason,
                destination=destination,
                transport_mode=transport_mode,
                remarks=remarks
            )
            messages.success(request, 'Submitted successfully.')
            return redirect('pending_leave') 
        except Student.DoesNotExist:
            messages.error(request, 'Enrollment number does not exist.')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return render(request, 'leave/add_leave.html')

@login_required(login_url='/authentication/login')
@permission_required('leave', 'add')
def check_enrollment(request):
    student_details = None
    error_message = None
    if request.method == 'POST':
        enrollment_number = request.POST.get('enrollment_number')
        try:
            student_details = Student.objects.get(roll=enrollment_number)
            if hasattr(request.user, 'profile') and request.user.profile.role.name == 'Student':
                if student_details.user != request.user:
                     raise PermissionDenied
        except Student.DoesNotExist:
            error_message = "Student Record not found."

    return render(request, 'leave/add_leave.html', {
        'student_details': student_details,
        'error_message': error_message,
    })

from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None

@login_required(login_url='/authentication/login')
@permission_required('leave', 'view')
def gate_pass_management(request):
    query = request.GET.get('q')
    status = request.GET.get('status')
    date = request.GET.get('date')
    
    gate_passes = GatePass.objects.select_related('leave_request__student').all()
    
    if query:
        gate_passes = gate_passes.filter(
            models.Q(gate_pass_no__icontains=query) |
            models.Q(leave_request__student__name__icontains=query) |
            models.Q(leave_request__student__roll__icontains=query)
        )
    
    if status:
        gate_passes = gate_passes.filter(status=status)
        
    if date:
        gate_passes = gate_passes.filter(leave_request__leave_date=date)
        
    return render(request, 'leave/gate_pass_management.html', {'gate_passes': gate_passes})

@login_required(login_url='/authentication/login')
def download_gate_pass_pdf(request, gp_id):
    if pisa is None:
        return HttpResponse('PDF generation dependency is not installed.', status=500)

    gp = get_object_or_404(GatePass, id=gp_id)
    
    # Security: Students can only download their own
    if hasattr(request.user, 'profile') and request.user.profile.role.name == 'Student':
        if gp.leave_request.student.user != request.user:
            raise PermissionDenied

    html = render_to_string('leave/gate_pass_pdf.html', {'gp': gp, 'student': gp.leave_request.student})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="GatePass_{gp.gate_pass_no}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    return response

@login_required(login_url='/authentication/login')
@permission_required('leave', 'view')
def leave_reports(request):
    # Today's students on leave
    today = date.today()
    on_leave_today = Student.objects.filter(status='On Leave')
    returned_today = HostelLeave.objects.filter(return_date=today, status='entered')
    expected_return = HostelLeave.objects.filter(return_date=today, status='approved')
    
    context = {
        'on_leave_today': on_leave_today,
        'returned_today': returned_today,
        'expected_return': expected_return,
        'today': today,
    }
    return render(request, 'leave/leave_reports.html', context)

@login_required(login_url='/authentication/login')    
@permission_required('leave', 'delete')
def delete_leave(request, leave_id):
    leave = get_object_or_404(HostelLeave, id=leave_id)
    if hasattr(request.user, 'profile') and request.user.profile.role.name == 'Student':
        if leave.student.user != request.user:
            raise PermissionDenied
    leave.delete()
    messages.success(request, 'Deleted successfully.')
    return redirect('leave_record')

