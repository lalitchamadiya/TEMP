from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from authentication.decorators import role_required
from student.models import Student

@login_required
@role_required('Warden', 'Super Admin')
def warden_dashboard(request):
    from hms.models import DutyAssignment
    assignment = DutyAssignment.objects.select_related('duty').filter(staff__user=request.user, is_active=True).first()
    
    students = Student.objects.all()
    if assignment and assignment.specific_location:
        students = students.filter(allocated_beds__room__building__name__icontains=assignment.specific_location).distinct()
    
    context = {
        'total_students': students.count(),
        'recent_students': students.order_by('-admission_date')[:10],
        'active_duty_assignment': assignment,
    }
    return render(request, 'warden/warden_dashboard.html', context)
