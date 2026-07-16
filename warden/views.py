from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from authentication.decorators import role_required
from authentication.models import WardenProfile
from student.models import Student
from room.models import HostelBlock, Floor, Room

@login_required
@role_required('Warden', 'Super Admin')
def warden_dashboard(request):
    from hms.models import DutyAssignment
    assignment = DutyAssignment.objects.select_related('duty', 'building', 'block', 'floor').filter(staff__user=request.user, is_active=True).first()
    
    warden_profile = None
    assigned_blocks = HostelBlock.objects.none()
    
    if hasattr(request.user, 'warden_profile'):
        warden_profile = request.user.warden_profile
        assigned_blocks = warden_profile.assigned_blocks.all()
    elif request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role.is_superadmin):
        assigned_blocks = HostelBlock.objects.all()

    # Get students in assigned blocks
    students = Student.objects.filter(bed__room__floor__block__in=assigned_blocks).distinct()
    rooms_qs = Room.objects.filter(floor__block__in=assigned_blocks)
    
    # Apply Duty location-scoped filtering override
    if assignment:
        if assignment.building:
            students = students.filter(bed__room__floor__building=assignment.building)
            rooms_qs = rooms_qs.filter(floor__building=assignment.building)
        if assignment.block:
            students = students.filter(bed__room__floor__block=assignment.block)
            rooms_qs = rooms_qs.filter(floor__block=assignment.block)
        if assignment.floor:
            students = students.filter(bed__room__floor=assignment.floor)
            rooms_qs = rooms_qs.filter(floor=assignment.floor)

    # Counts
    total_students = students.count()
    total_rooms = rooms_qs.count()
    
    context = {
        'assigned_blocks': assigned_blocks,
        'total_students': total_students,
        'total_rooms': total_rooms,
        'recent_students': students.order_by('-admission_date')[:10],
        'active_duty_assignment': assignment,
    }
    return render(request, 'warden/warden_dashboard.html', context)
