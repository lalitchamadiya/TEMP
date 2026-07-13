from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.db import transaction, IntegrityError
import secrets

from .forms import StudentForm
from .models import Student


from django.db.models import Q, Count
from django.db.models.functions import ExtractMonth
from .models import DEPARTMENT_CHOICES, COURSE_CHOICES, STATUS_CHOICES

from django.utils import timezone
import json
from authentication.decorators import role_required, permission_required
from django.core.exceptions import PermissionDenied



@login_required
@permission_required('student', 'view')
def student_list(request):
    # Student role isolation: Redirect to their own profile if they try to access list
    if hasattr(request.user, 'profile') and request.user.profile.role.name == 'Student':
        try:
            student_obj = Student.objects.get(user=request.user)
            return redirect('view_student', pk=student_obj.pk)
        except Student.DoesNotExist:
            raise PermissionDenied("Student record not found for this user.")

    query = request.GET.get('q')
    dept = request.GET.get('department')
    course = request.GET.get('course')
    status = request.GET.get('status')
    
    students = Student.objects.select_related('user').all()
    
    if query:
        students = students.filter(
            Q(name__icontains=query) |
            Q(roll__icontains=query) |
            Q(email__icontains=query) |
            Q(phone_number__icontains=query)
        )
    
    if dept:
        students = students.filter(department=dept)
    
    if course:
        students = students.filter(course=course)
        
    if status:
        students = students.filter(status=status)
        
    context = {
        'students': students,
        'departments': [choice[0] for choice in DEPARTMENT_CHOICES],
        'courses': [choice[0] for choice in COURSE_CHOICES],
        'statuses': [choice[0] for choice in STATUS_CHOICES],
        'current_filters': {
            'q': query,
            'department': dept,
            'course': course,
            'status': status,
        }
    }
    return render(request, 'student/student_list.html', context)


@transaction.atomic
@login_required
@permission_required('student', 'add')
def create_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)

            roll = form.cleaned_data['roll']
            email = form.cleaned_data['email']
            try:
                user = User.objects.create_user(
                    username=roll,
                    email=email,
                    password='User1234',
                )
            except IntegrityError:
                if User.objects.filter(username=roll).exists():
                    form.add_error('roll', 'A user with this enrollment number already exists.')
                else:
                    form.add_error('email', 'A user with this email already exists.')
            else:
                group, _ = Group.objects.get_or_create(name='Students')
                user.groups.add(group)
                student.user = user
                student.save()
                messages.success(request, 'Student created successfully.')
                return redirect('student_list')
    else:
        form = StudentForm()
    return render(request, 'student/create_student.html', {'form': form})


@transaction.atomic
@login_required
@permission_required('student', 'edit')
def update_student(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student = form.save(commit=False)
            new_roll = form.cleaned_data['roll']
            new_email = form.cleaned_data['email']
            if student.user:
                user_updated = False
                if new_roll != student.user.username:
                    if User.objects.filter(username=new_roll).exclude(pk=student.user.pk).exists():
                        form.add_error('roll', 'Another user with this enrollment number already exists.')
                        return render(request, 'student/update_student.html', {'form': form})
                    student.user.username = new_roll
                    user_updated = True
                if new_email != student.user.email:
                    if User.objects.filter(email=new_email).exclude(pk=student.user.pk).exists():
                        form.add_error('email', 'Another user with this email already exists.')
                        return render(request, 'student/update_student.html', {'form': form})
                    student.user.email = new_email
                    user_updated = True
                if user_updated:
                    student.user.save()
            student.save()
            messages.success(request, 'Student updated successfully.')
            return redirect('student_list')
    else:
        form = StudentForm(instance=student)
    return render(request, 'student/update_student.html', {'form': form})


from django.http import JsonResponse

@login_required
def check_roll_number(request):
    roll = request.GET.get('roll', '').strip()
    student_id = request.GET.get('student_id', '').strip()
    
    if not roll:
        return JsonResponse({'available': True})
        
    qs = Student.objects.filter(roll=roll)
    if student_id:
        qs = qs.exclude(pk=student_id)
        
    user_qs = User.objects.filter(username=roll)
    if student_id:
        try:
            s_obj = Student.objects.get(pk=student_id)
            if s_obj.user:
                user_qs = user_qs.exclude(pk=s_obj.user.pk)
        except Student.DoesNotExist:
            pass
            
    is_available = not qs.exists() and not user_qs.exists()
    return JsonResponse({'available': is_available})


@login_required
@permission_required('student', 'view')
def view_student(request, pk):
    student = get_object_or_404(Student, pk=pk)

    
    # Student role isolation: Can only view their own record
    if hasattr(request.user, 'profile') and request.user.profile.role.name == 'Student':
        if student.user != request.user:
            raise PermissionDenied("You are not authorized to view this record.")

    return render(request, 'student/view_student.html', {'student': student})


@login_required
@permission_required('student', 'delete')
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        # deleting the user cascades to the Student record
        if student.user:
            student.user.delete()
        messages.success(request, 'Student deleted successfully.')
        return redirect('student_list')
    return render(request, 'student/confirm_delete.html', {'student': student})