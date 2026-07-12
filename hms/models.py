from django.db import models
from django.contrib.auth.models import User
from student.models import Student
from room.models import HostelBuilding, HostelBlock, Floor, Room, Bed
from django.utils import timezone

class StaffProfile(models.Model):
    DESIGNATION_CHOICES = [
        ('warden', 'Hostel Warden'),
        ('cleaner', 'Cleaning Staff'),
        ('chef', 'Kitchen Chef'),
        ('helpers', 'Kitchen Helper'),
        ('guard', 'Security Guard'),
        ('maintenance', 'Maintenance Technician'),
        ('admin', 'Admin Coordinator'),
    ]
    SHIFT_CHOICES = [
        ('morning', 'Morning Shift (6 AM - 2 PM)'),
        ('evening', 'Evening Shift (2 PM - 10 PM)'),
        ('night', 'Night Shift (10 PM - 6 AM)'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
    ]
    PERFORMANCE_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('needs_improvement', 'Needs Improvement'),
    ]

    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_profile')
    hostel = models.ForeignKey('authentication.Hostel', on_delete=models.CASCADE, related_name='staff', null=True, blank=True)
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    designation = models.CharField(max_length=50, choices=DESIGNATION_CHOICES)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, default='morning')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    performance = models.CharField(max_length=30, choices=PERFORMANCE_CHOICES, default='good')
    doj = models.DateField(default=timezone.now)
    documents = models.CharField(max_length=255, blank=True, help_text="List of submitted docs, e.g. Aadhar, Police verification")

    def __str__(self):
        return f"{self.name} - {self.get_designation_display()}"


class Visitor(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved Entry'),
        ('denied', 'Entry Denied'),
        ('completed', 'Checked Out'),
    ]
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='visitors')
    relation = models.CharField(max_length=50, help_text="Relation to the student")
    visit_date = models.DateField(default=timezone.now)
    purpose = models.CharField(max_length=255)
    entry_time = models.TimeField(null=True, blank=True)
    exit_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    pass_code = models.CharField(max_length=20, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pass_code:
            import random
            self.pass_code = f"VIS-{random.randint(100000, 999999)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - Visiting {self.student.name}"


class InventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('furniture', 'Furniture'),
        ('assets', 'Assets/Appliances'),
        ('stock', 'Stock/Ration'),
        ('consumables', 'Consumables/Cleaning'),
    ]
    STATUS_CHOICES = [
        ('good', 'Good Condition'),
        ('damaged', 'Damaged'),
        ('maintenance', 'Under Maintenance'),
        ('oos', 'Out of Stock'),
    ]
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    quantity = models.IntegerField(default=1)
    available_quantity = models.IntegerField(default=1)
    vendor_name = models.CharField(max_length=150, blank=True)
    vendor_contact = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='good')
    purchase_date = models.DateField(default=timezone.now)
    purchase_order_no = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class ComplaintTicket(models.Model):
    CATEGORY_CHOICES = [
        ('room', 'Room Maintenance'),
        ('mess', 'Mess & Food'),
        ('electricity', 'Electricity & Power'),
        ('internet', 'Internet & Wi-Fi'),
        ('cleaning', 'Cleaning & Hygiene'),
        ('other', 'Other Issues'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Ticket'),
        ('assigned', 'Ticket Assigned'),
        ('in_progress', 'Resolution in Progress'),
        ('resolved', 'Resolved'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='complaints')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    assigned_to = models.ForeignKey(StaffProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    feedback = models.TextField(blank=True, help_text="Feedback from the student after resolution")

    def __str__(self):
        return f"#{self.id or 'New'} - {self.title} ({self.get_status_display()})"


class SecurityGuard(models.Model):
    hostel = models.ForeignKey('authentication.Hostel', on_delete=models.CASCADE, related_name='guards', null=True, blank=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    gate_no = models.CharField(max_length=50, default='Main Gate 1')
    shift = models.CharField(max_length=50, default='morning')
    status = models.CharField(max_length=20, default='active')

    def __str__(self):
        return f"Guard: {self.name} ({self.gate_no})"


class IncidentReport(models.Model):
    TITLE_CHOICES = [
        ('theft', 'Theft Alert'),
        ('trespassing', 'Unauthorized Entry'),
        ('damage', 'Property Damage'),
        ('disorder', 'Disorderly Conduct'),
        ('medical', 'Medical Emergency'),
        ('fire', 'Fire Alarm'),
        ('other', 'Other Incident'),
    ]
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High/Critical'),
    ]
    title = models.CharField(max_length=50, choices=TITLE_CHOICES, default='other')
    description = models.TextField()
    guard = models.ForeignKey(SecurityGuard, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='low')
    action_taken = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_title_display()} - {self.date}"


class DutyAssignment(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='duties')
    duty_title = models.CharField(max_length=100, help_text="e.g. Floor Supervisor, Guard, Kitchen Help")
    building = models.ForeignKey(HostelBuilding, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_duties')
    block = models.ForeignKey(HostelBlock, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_duties')
    floor = models.ForeignKey(Floor, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_duties')
    specific_location = models.CharField(max_length=150, blank=True, help_text="e.g. Main Gate 1, Kitchen, Mess hall")
    shift_start = models.TimeField(null=True, blank=True)
    shift_end = models.TimeField(null=True, blank=True)
    description = models.TextField(blank=True, help_text="Specific instructions or notes")
    assigned_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'duty_assignment'
        ordering = ['-assigned_date', 'staff__name']

    def __str__(self):
        dest = ""
        if self.building:
            dest += f" {self.building.name}"
        if self.block:
            dest += f" Block {self.block.name}"
        if self.floor:
            dest += f" Floor {self.floor.floor_number}"
        if self.specific_location:
            dest += f" ({self.specific_location})"
        return f"{self.staff.name} - {self.duty_title}:{dest or ' General'}"

