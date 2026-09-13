from django.db import models
from django.contrib.auth.models import User
from student.models import Student


class HostelBuilding(models.Model):
    GENDER_CHOICES = [
        ('Boys', 'Boys Wing / Male'),
        ('Girls', 'Girls Wing / Female'),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Boys')
    total_floors = models.IntegerField(default=3)
    blocks = models.CharField(max_length=200, default='Block A, Block B', blank=True, null=True, help_text='Comma-separated blocks e.g. Block A, Block B')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def pk_str(self):
        return str(self.pk)

    def get_current_fee(self, academic_year=None):
        if academic_year:
            year_str = str(academic_year).strip()
            fee_obj = self.fee_structures.filter(academic_year=year_str, is_active=True).first()
            if not fee_obj:
                fee_obj = self.fee_structures.filter(academic_year__icontains=year_str, is_active=True).first()
            if fee_obj:
                return fee_obj

        return self.fee_structures.filter(is_active=True).order_by('-academic_year').first()


class BuildingFeeStructure(models.Model):
    FEE_TYPE_CHOICES = [
        ('MONTHLY_PER_STUDENT', 'Monthly – Per Student'),
        ('YEARLY_PER_STUDENT', 'Yearly – Per Student'),
    ]

    building = models.ForeignKey(HostelBuilding, on_delete=models.CASCADE, related_name='fee_structures')
    academic_year = models.CharField(max_length=20, default='2026–2027')
    fee_type = models.CharField(max_length=30, choices=FEE_TYPE_CHOICES, default='MONTHLY_PER_STUDENT')
    monthly_fee_per_student = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    yearly_fee_per_student = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'building_fee_structure'
        unique_together = ('building', 'academic_year')
        ordering = ['-academic_year']

    def __str__(self):
        if self.fee_type == 'YEARLY_PER_STUDENT':
            return f"{self.building.name} ({self.academic_year}): ₹{self.yearly_fee_per_student}/year"
        return f"{self.building.name} ({self.academic_year}): ₹{self.monthly_fee_per_student}/month"

    @property
    def get_fee_amount(self):
        if self.fee_type == 'YEARLY_PER_STUDENT':
            return self.yearly_fee_per_student
        return self.monthly_fee_per_student


class Room(models.Model):
    ROOM_TYPE_CHOICES = [
        ('2_BED', '2 BED (Double Sharing)'),
        ('4_BED', '4 BED (Quad Sharing)'),
        ('CUSTOM', 'CUSTOM (Specify Capacity)'),
    ]
    CATEGORY_CHOICES = [
        ('GENERAL', 'General Student'),
        ('DELUXE', 'Deluxe Premium'),
        ('STAFF', 'Staff / Warden'),
    ]
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available / Active'),
        ('MAINTENANCE', 'Under Maintenance'),
    ]
    GENDER_CHOICES = [
        ('Boys', 'Boys Wing / Male'),
        ('Girls', 'Girls Wing / Female'),
    ]

    building = models.ForeignKey(HostelBuilding, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=20)
    room_name = models.CharField(max_length=100, blank=True, null=True)
    block = models.CharField(max_length=10, default='A')
    floor = models.IntegerField(default=1)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='2_BED')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='GENERAL')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Boys')
    capacity = models.IntegerField(default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    is_ac = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.building.name} - Room {self.room_number}"


class Bed(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='beds')
    bed_number = models.CharField(max_length=10)
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='allocated_beds')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"Room {self.room.room_number} - Bed {self.bed_number}"