import uuid
import hashlib
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from student.models import Student
from room.models import HostelBuilding, Room, Bed


class FeeCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True, null=True)
    is_refundable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Fee Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class FeeComponent(models.Model):
    TYPE_CHOICES = [
        ('FIXED', 'Fixed Amount'),
        ('PERCENTAGE', 'Percentage of Base'),
        ('VARIABLE', 'Variable / Custom'),
    ]

    name = models.CharField(max_length=100)
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, related_name='components')
    component_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='FIXED')
    default_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_mandatory = models.BooleanField(default=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class FeeStructure(models.Model):
    APPLICABLE_FOR_CHOICES = [
        ('BOYS', 'Boys Hostel'),
        ('GIRLS', 'Girls Hostel'),
        ('STAFF', 'Staff Hostel'),
        ('GUEST', 'Guest'),
    ]
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('ARCHIVED', 'Archived'),
    ]
    FREQUENCY_CHOICES = [
        ('MONTHLY', 'Monthly (12 Installments)'),
        ('QUARTERLY', 'Quarterly (4 Installments)'),
        ('HALF_YEARLY', 'Half-Yearly (2 Installments)'),
        ('YEARLY', 'Yearly (1 Installment)'),
        ('ONE_TIME', 'One Time Payment'),
    ]
    LATE_FEE_CHOICES = [
        ('NONE', 'No Late Fee'),
        ('FIXED', 'Fixed Amount'),
        ('PERCENTAGE', 'Percentage'),
        ('DAILY', 'Daily Charge'),
    ]

    name = models.CharField(max_length=150)
    building = models.ForeignKey(HostelBuilding, on_delete=models.CASCADE, related_name='fee_structures')
    room_type = models.CharField(max_length=50, default='2_BED')
    academic_year = models.CharField(max_length=20, default='2026-27')
    applicable_for = models.CharField(max_length=20, choices=APPLICABLE_FOR_CHOICES, default='BOYS')
    version = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PUBLISHED')

    # Payment Configuration
    payment_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='MONTHLY')
    due_day = models.IntegerField(default=5, help_text="Day of the month e.g. 5th")
    late_fee_rule = models.CharField(max_length=20, choices=LATE_FEE_CHOICES, default='NONE')
    late_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    grace_period_days = models.IntegerField(default=5)
    allow_partial = models.BooleanField(default=True)
    max_partial_percent = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)
    enable_online = models.BooleanField(default=True)
    offline_modes = models.CharField(max_length=100, default='Cash, UPI, Bank Transfer, Cheque, Card')

    # Tax
    include_gst = models.BooleanField(default=False)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)

    # Base calculated amount
    total_base_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_fee_with_gst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('building', 'room_type', 'academic_year', 'version')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - v{self.version} ({self.academic_year})"


class FeeStructureComponent(models.Model):
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='components')
    fee_component = models.ForeignKey(FeeComponent, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order = models.IntegerField(default=1)
    is_gst_applicable = models.BooleanField(default=False)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.fee_structure.name} -> {self.fee_component.name}: ₹{self.amount}"


class FeeDiscountRule(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('SCHOLARSHIP', 'Scholarship'),
        ('SIBLING', 'Sibling Discount'),
        ('MERIT', 'Merit Discount'),
        ('SPECIAL', 'Special Discount'),
        ('EMPLOYEE_CHILD', 'Employee Child'),
        ('CUSTOM', 'Custom Discount'),
    ]
    CALC_CHOICES = [
        ('PERCENTAGE', 'Percentage'),
        ('FIXED', 'Fixed Amount'),
    ]

    name = models.CharField(max_length=100)
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='discount_rules', null=True, blank=True)
    discount_type = models.CharField(max_length=30, choices=DISCOUNT_TYPE_CHOICES, default='SCHOLARSHIP')
    calculation_type = models.CharField(max_length=20, choices=CALC_CHOICES, default='FIXED')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    valid_until = models.DateField(null=True, blank=True)
    remarks = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_discount_type_display()})"


class FeeFineRule(models.Model):
    FINE_TYPE_CHOICES = [
        ('LATE_PAYMENT', 'Late Payment Fine'),
        ('LOST_KEY', 'Lost Key Fine'),
        ('DAMAGE', 'Room Damage Fine'),
        ('ROOM_CLEANING', 'Room Cleaning Fine'),
        ('MESS', 'Mess Fine'),
        ('CUSTOM', 'Custom Fine'),
    ]
    CALC_CHOICES = [
        ('PER_DAY', 'Per Day Charge'),
        ('FIXED', 'Fixed Amount'),
        ('PERCENTAGE', 'Percentage of Balance'),
    ]

    name = models.CharField(max_length=100)
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='fine_rules', null=True, blank=True)
    fine_type = models.CharField(max_length=30, choices=FINE_TYPE_CHOICES, default='LATE_PAYMENT')
    calculation_type = models.CharField(max_length=20, choices=CALC_CHOICES, default='FIXED')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    grace_period_days = models.IntegerField(default=5)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name}: ₹{self.amount}"


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ISSUED', 'Issued'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Fully Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True) # e.g. HMS-INV-2026-000001
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='invoices')
    bed = models.ForeignKey(Bed, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.SET_NULL, null=True, blank=True)
    academic_year = models.CharField(max_length=20, default='2026-27')

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pending_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ISSUED')
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    is_locked = models.BooleanField(default=True, help_text="Immutable after issue")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invoice_number} - {self.student.name} (₹{self.total_amount})"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    fee_component = models.ForeignKey(FeeComponent, on_delete=models.SET_NULL, null=True, blank=True)
    component_name = models.CharField(max_length=100)
    base_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.invoice.invoice_number} -> {self.component_name}: ₹{self.net_amount}"


class StudentInstallment(models.Model):
    STATUS_CHOICES = [
        ('UNPAID', 'Unpaid'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='installments')
    installment_no = models.IntegerField(default=1)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNPAID')

    class Meta:
        ordering = ['installment_no']

    def __str__(self):
        return f"Inst #{self.installment_no} ({self.invoice.invoice_number}) - ₹{self.amount}"


class PaymentTransaction(models.Model):
    METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI Payment'),
        ('BANK', 'Bank Transfer / NEFT / RTGS'),
        ('CHEQUE', 'Cheque'),
        ('CARD', 'Debit / Credit Card'),
    ]
    STATUS_CHOICES = [
        ('SUCCESSFUL', 'Successful'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    transaction_id = models.CharField(max_length=60, unique=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='transactions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='transactions')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fine_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='UPI')
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    cheque_no = models.CharField(max_length=50, blank=True, null=True)
    upi_ref = models.CharField(max_length=100, blank=True, null=True)

    payment_date = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    receipt_file = models.FileField(upload_to='receipts/', blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUCCESSFUL')

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.transaction_id} - {self.student.name} (₹{self.amount_paid})"


class Receipt(models.Model):
    receipt_number = models.CharField(max_length=60, unique=True) # e.g. NBNH-2026-07-000001
    transaction = models.OneToOneField(PaymentTransaction, on_delete=models.CASCADE, related_name='receipt')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='receipts')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='receipts')
    qr_code_hash = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.qr_code_hash:
            raw = f"{self.receipt_number}-{self.student.student_id}-{self.transaction.amount_paid}-{timezone.now().timestamp()}"
            self.qr_code_hash = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.receipt_number


class Refund(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved & Processed'),
        ('REJECTED', 'Rejected'),
    ]

    refund_number = models.CharField(max_length=60, unique=True) # e.g. NBNH-REF-2026-07-000001
    original_transaction = models.ForeignKey(PaymentTransaction, on_delete=models.CASCADE, related_name='refunds')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='refunds')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPROVED')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.refund_number} (₹{self.amount})"


class StudentLedger(models.Model):
    TYPE_CHOICES = [
        ('INVOICE', 'Invoice Issued (+)'),
        ('PAYMENT', 'Payment Received (-)'),
        ('REFUND', 'Refund Issued (+)'),
        ('DISCOUNT', 'Discount Adjustment (-)'),
        ('FINE', 'Fine Charge (+)'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='ledger_entries')
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    reference_no = models.CharField(max_length=60)
    debit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    credit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    running_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']

    def __str__(self):
        return f"{self.student.name} | {self.transaction_type} | {self.reference_no} | Bal: ₹{self.running_balance}"


class PaymentGatewayLog(models.Model):
    gateway_name = models.CharField(max_length=50, default='Razorpay')
    order_id = models.CharField(max_length=100)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=30, default='INITIATED')
    response_payload = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.gateway_name} - {self.order_id} ({self.status})"
