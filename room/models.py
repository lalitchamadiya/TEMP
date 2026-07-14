from django.db import models
from student.models import Student


GENDER_CHOICES = [
    ('BOY', 'Boys'),
    ('GIRL', 'Girls'),
    ('MIXED', 'Mixed'),
]

ROOM_TYPE_CHOICES = [
    ('SINGLE', 'Single (1 Bed)'),
    ('DOUBLE', 'Double (2 Beds)'),
    ('TRIPLE', 'Triple (3 Beds)'),
    ('DORMITORY', 'Dormitory'),
    ('DELUXE', 'Deluxe'),
    ('AC', 'AC Room'),
    ('NON_AC', 'Non-AC Room'),
    ('CUSTOM', 'Custom'),
]

ROOM_CATEGORY_CHOICES = [
    ('GENERAL', 'General'),
    ('VIP', 'VIP / Premium'),
    ('STAFF', 'Staff Quarters'),
    ('RESERVED', 'Reserved'),
]

ROOM_STATUS_CHOICES = [
    ('ACTIVE', 'Active'),
    ('MAINTENANCE', 'Under Maintenance'),
    ('INACTIVE', 'Inactive'),
]

BLOCK_CHOICES = [
    ('A', 'Block A'),
    ('B', 'Block B'),
    ('C', 'Block C'),
    ('D', 'Block D'),
    ('E', 'Block E'),
    ('F', 'Block F'),
    ('NORTH', 'North Wing'),
    ('SOUTH', 'South Wing'),
    ('EAST', 'East Wing'),
    ('WEST', 'West Wing'),
]

# Capacity map per room type (defaults; overridable)
CAPACITY_MAP = {
    'SINGLE': 1,
    'DOUBLE': 2,
    'TRIPLE': 3,
    'DORMITORY': 10,
    'DELUXE': 2,
    'AC': 2,
    'NON_AC': 2,
    'CUSTOM': 0,
}

DEFAULT_ROOM_TYPE_PRICES = {
    'SINGLE': 8000.00,
    'DOUBLE': 6000.00,
    'TRIPLE': 5000.00,
    'DORMITORY': 3000.00,
    'DELUXE': 9000.00,
    'AC': 6000.00,
    'NON_AC': 6000.00,
}

DEFAULT_CATEGORY_MULTIPLIERS = {
    'GENERAL': 1.00,
    'VIP': 1.30,
    'STAFF': 0.00,
    'RESERVED': 0.00,
}


class RoomTypePricing(models.Model):
    hostel = models.ForeignKey('authentication.Hostel', on_delete=models.CASCADE, related_name='room_type_pricings', null=True, blank=True)
    room_type = models.CharField(max_length=50)
    label = models.CharField(max_length=100, blank=True, null=True)
    base_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('hostel', 'room_type')
        db_table = 'room_type_pricing'

    def __str__(self):
        return f"{self.label or self.room_type}: {self.base_rent}"


class RoomCategoryPricing(models.Model):
    hostel = models.ForeignKey('authentication.Hostel', on_delete=models.CASCADE, related_name='room_category_pricings', null=True, blank=True)
    category = models.CharField(max_length=50)
    label = models.CharField(max_length=100, blank=True, null=True)
    multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('hostel', 'category')
        db_table = 'room_category_pricing'

    def __str__(self):
        return f"{self.label or self.category}: {self.multiplier}"




class HostelBuilding(models.Model):
    hostel = models.ForeignKey('authentication.Hostel', on_delete=models.CASCADE, related_name='buildings', null=True, blank=True)

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='MIXED')
    total_floors = models.PositiveIntegerField(default=1)
    warden = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='managed_buildings'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hostel_building'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def occupancy_count(self):
        return self.rooms.filter(status='ACTIVE').count()


class HostelBlock(models.Model):
    """Block lives inside a Building (e.g. Building A → Block A, Block B)"""
    building = models.ForeignKey(
        HostelBuilding, on_delete=models.CASCADE,
        related_name='blocks', null=True, blank=True
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    block_manager = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='managed_blocks'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('building', 'name')

    def __str__(self):
        if self.building:
            return f"{self.building.name} – Block {self.name}"
        return self.name


class Floor(models.Model):
    CLEANING_STATUS = [
        ('clean', 'Clean'),
        ('dirty', 'Needs Cleaning'),
        ('in_progress', 'Cleaning In Progress'),
    ]

    block = models.ForeignKey(HostelBlock, on_delete=models.CASCADE, related_name='floors')
    building = models.ForeignKey(
        HostelBuilding, on_delete=models.CASCADE, related_name='floors',
        null=True, blank=True
    )
    floor_number = models.IntegerField()
    capacity = models.PositiveIntegerField(default=0, help_text='Max rooms on this floor')
    cleaning_status = models.CharField(
        max_length=20, choices=CLEANING_STATUS, default='clean'
    )
    maintenance_note = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['floor_number']
        unique_together = ('block', 'floor_number')

    def __str__(self):
        if self.building:
            return f"{self.building.name} – Blk {self.block.name} – Floor {self.floor_number}"
        return f"{self.block.name} – Floor {self.floor_number}"


class Room(models.Model):
    # Legacy choices kept for backward compat
    ROOM_TYPES = (
        ('2B', '2 Bed'),
        ('4B', '4 Bed'),
    )
    GENDER = (
        ('BOY', 'BOYS'),
        ('GIRL', 'GIRLS'),
    )

    # --- Location ---
    hostel = models.ForeignKey('authentication.Hostel', on_delete=models.CASCADE, related_name='rooms', null=True, blank=True)
    building = models.ForeignKey(
        HostelBuilding, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rooms'
    )
    block = models.CharField(max_length=10, choices=BLOCK_CHOICES, blank=True)
    floor = models.ForeignKey(
        Floor, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rooms'
    )

    # --- Identity ---
    room_number = models.CharField(max_length=20)
    room_name = models.CharField(max_length=100, blank=True, help_text="Optional friendly name")

    # --- Classification ---
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='DOUBLE')
    category = models.CharField(
        max_length=20, choices=ROOM_CATEGORY_CHOICES, default='GENERAL'
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='BOY')

    # --- Occupancy ---
    capacity = models.PositiveIntegerField(default=2, help_text="Number of beds in the room")
    is_ac = models.BooleanField(default=False)
    attached_bathroom = models.BooleanField(default=False)

    # --- Status ---
    status = models.CharField(
        max_length=20, choices=ROOM_STATUS_CHOICES, default='ACTIVE'
    )

    # --- Meta ---
    description = models.TextField(blank=True)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'room'
        ordering = ['room_number']
        unique_together = ('building', 'room_number')

    def __str__(self):
        parts = [self.room_number]
        if self.room_name:
            parts.append(self.room_name)
        return ' – '.join(parts)

    @property
    def is_available(self):
        return self.status == 'ACTIVE'

    @property
    def default_capacity(self):
        return CAPACITY_MAP.get(self.room_type, 2)

    def calculate_suggested_rent(self):
        """
        Calculate suggested monthly rent based on:
        - Room Type Base Rent (dynamic if configured)
        - Category Multiplier (dynamic if configured)
        - AC Amenity Charge
        """
        if self.room_type == 'CUSTOM':
            return self.monthly_rent

        # Base Rent Map
        base_rent = None
        if self.hostel:
            try:
                pricing = RoomTypePricing.objects.get(hostel=self.hostel, room_type=self.room_type)
                if pricing.is_active:
                    base_rent = pricing.base_rent
            except RoomTypePricing.DoesNotExist:
                pass
        
        if base_rent is None:
            try:
                pricing = RoomTypePricing.objects.get(hostel__isnull=True, room_type=self.room_type)
                if pricing.is_active:
                    base_rent = pricing.base_rent
            except RoomTypePricing.DoesNotExist:
                base_rent = DEFAULT_ROOM_TYPE_PRICES.get(self.room_type, 0.00)

        # Category Multipliers
        multiplier = None
        if self.hostel:
            try:
                pricing = RoomCategoryPricing.objects.get(hostel=self.hostel, category=self.category)
                if pricing.is_active:
                    multiplier = pricing.multiplier
            except RoomCategoryPricing.DoesNotExist:
                pass

        if multiplier is None:
            try:
                pricing = RoomCategoryPricing.objects.get(hostel__isnull=True, category=self.category)
                if pricing.is_active:
                    multiplier = pricing.multiplier
            except RoomCategoryPricing.DoesNotExist:
                multiplier = DEFAULT_CATEGORY_MULTIPLIERS.get(self.category, 0.00)

        # Amenity Charge (AC)
        amenity_charge = 0
        if self.is_ac and self.category not in ['STAFF', 'RESERVED']:
            amenity_charge = 1500

        # Calculations
        from decimal import Decimal
        return Decimal(base_rent) * Decimal(multiplier) + Decimal(amenity_charge)

    def save(self, *args, **kwargs):
        if self.building:
            self.gender = self.building.gender

        # Auto-calculate rent for non-custom types
        if self.room_type != 'CUSTOM':
            computed = self.calculate_suggested_rent()
            if self.category == 'STAFF':
                # Staff rooms can have custom rent, default to 0 if not set
                if self.monthly_rent is None or self.monthly_rent == 0:
                    self.monthly_rent = 0
            else:
                self.monthly_rent = computed
        super().save(*args, **kwargs)


class Bed(models.Model):
    BED_STATUS = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('maintenance', 'Under Maintenance'),
    ]

    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='beds')
    bed_number = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=BED_STATUS, default='available')
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Bed {self.bed_number} in Room {self.room.room_number}"

    class Meta:
        unique_together = ('room', 'bed_number')


class BedAllocation(models.Model):
    """Full allocation history for each Bed — tracks who occupied it and when."""
    bed = models.ForeignKey(Bed, on_delete=models.CASCADE, related_name='allocations')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='bed_allocations')
    allocated_at = models.DateTimeField(default=None)
    vacated_at = models.DateTimeField(null=True, blank=True)
    allocated_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='bed_allocations_made'
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-allocated_at']

    def __str__(self):
        return f"{self.student.name} @ Bed {self.bed} ({self.allocated_at:%Y-%m-%d})"