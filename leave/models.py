from django.db import models
from django.contrib.auth.models import User
from student.models import Student

class HostelLeave(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    leave_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    return_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    total_days = models.IntegerField(default=1)
    destination = models.CharField(max_length=255, blank=True, null=True)
    transport_mode = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approval_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.leave_date} ({self.status})"

class LeaveRequest(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    reason = models.TextField()
    leave_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('entered', 'Entered Hostel'),
        ],
        default='pending'
    )

    def __str__(self):
        return f"{self.student} - {self.status}"

class GatePass(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Cancelled', 'Cancelled'),
    ]
    gate_pass_no = models.CharField(max_length=50, unique=True)
    leave_request = models.OneToOneField(HostelLeave, on_delete=models.CASCADE, related_name='gate_pass')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.gate_pass_no

    class Meta:
        verbose_name_plural = "Gate Passes"