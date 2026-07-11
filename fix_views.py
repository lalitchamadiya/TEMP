import os

view_file = r'f:\Django\Hostel_Management_System\student_app\views.py'
with open(view_file, 'r') as f:
    content = f.read()

new_view = """
@login_required(login_url='/authentication/login')
def student_dashboard(request):
    student = get_object_or_404(Student, email=request.user.email)
    
    # Bed/Room info
    bed = student.bed_set.first()
    
    # Fee Info
    total_fee = FeeStructure.objects.aggregate(total=Sum('amount'))['total'] or 0
    paid_fee = Payment.objects.filter(student=student).aggregate(total_paid=Sum('amount'))['total_paid'] or 0
    pending_fee = total_fee - paid_fee
    payment_percentage = (paid_fee / total_fee * 100) if total_fee > 0 else 0
    
    # Leave Info
    recent_leaves = HostelLeave.objects.filter(student=student).order_by('-created_at')[:5]
    
    context = {
        'student': student,
        'bed': bed,
        'total_fee': total_fee,
        'paid_fee': paid_fee,
        'pending_fee': pending_fee,
        'payment_percentage': payment_percentage,
        'recent_leaves': recent_leaves,
    }
    return render(request, 'student_app/student_dashboard.html', context)

"""

target = "@login_required(login_url='/authentication/login')\ndef student_profile(request):"
if target in content:
    new_content = content.replace(target, new_view + "\n" + target)
    with open(view_file, 'w') as f:
        f.write(new_content)
    print('Successfully updated views.py')
else:
    print('Target not found in views.py')
