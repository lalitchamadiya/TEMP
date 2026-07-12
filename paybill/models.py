from django.db import models
from django.db.models import Sum
from student.models import Student

class GatewayConfig(models.Model):
    GATEWAY_CHOICES = [
        ('razorpay', 'Razorpay'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('phonepe', 'PhonePe'),
        ('demo', 'Demo Gateway (Simulation)'),
    ]
    name = models.CharField(max_length=20, choices=GATEWAY_CHOICES, unique=True)
    is_active = models.BooleanField(default=True)
    api_key = models.CharField(max_length=255)
    api_secret = models.CharField(max_length=255)
    webhook_secret = models.CharField(max_length=255, blank=True, null=True)
    webhook_url = models.URLField(blank=True, null=True)
    is_live = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.get_name_display()} ({'Live' if self.is_live else 'Test'})"

class Payment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SUCCESSFUL', 'Successful'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    hostel = models.ForeignKey('authentication.Hostel', on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    transaction_id = models.CharField(max_length=50, unique=True)
    gateway_name = models.CharField(max_length=20, blank=True, null=True)
    gateway_order_id = models.CharField(max_length=100, blank=True, null=True)
    gateway_payment_id = models.CharField(max_length=100, blank=True, null=True)
    enrollment_number = models.CharField(max_length=20)
    user_name = models.CharField(max_length=100)
    contact_no = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, default='UPI') # UPI, Card, NetBanking, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    transaction_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    receipt_no = models.CharField(max_length=20, unique=True, null=True, blank=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    fee_breakdown = models.JSONField(null=True, blank=True) # For detailed breakdown
    
    def save(self, *args, **kwargs):
        is_new_success = False
        if self.transaction_status == 'SUCCESSFUL':
            if not self.pk:
                is_new_success = True
            else:
                old = Payment.objects.filter(pk=self.pk).first()
                if old and old.transaction_status != 'SUCCESSFUL':
                    is_new_success = True

        if not self.receipt_no and self.transaction_status == 'SUCCESSFUL':
            last_receipt = Payment.objects.filter(receipt_no__isnull=False).order_by('-receipt_no').first()
            if last_receipt and last_receipt.receipt_no.startswith('REC'):
                 try:
                     num = int(last_receipt.receipt_no[3:]) + 1
                 except ValueError:
                     num = 10001
            else:
                num = 10001
            self.receipt_no = f"REC{num}"
            
        super().save(*args, **kwargs)
        
        if is_new_success and self.student:
            from decimal import Decimal
            from room.models import Bed
            bed = Bed.objects.filter(student=self.student).first()
            if bed:
                base_paid = self.amount
                if self.fee_breakdown and 'base_amount' in self.fee_breakdown:
                    try:
                        base_paid = Decimal(str(self.fee_breakdown['base_amount']))
                    except Exception:
                        pass
                bed.paid_amount = (bed.paid_amount or 0) + base_paid
                bed.remaining_amount = max(0, bed.total_amount - bed.paid_amount)
                bed.save()

    def __str__(self):
        return f"{self.enrollment_number} - {self.amount} - {self.transaction_status}"
    
class FeeStructure(models.Model):
    FEE_TYPES = [
        ('rent', 'Hostel Rent'),
        ('deposit', 'Security Deposit'),
        ('electricity', 'Electricity Charges'),
        ('mess', 'Mess Charges'),
        ('maintenance', 'Maintenance Charges'),
        ('other', 'Other Charges'),
    ]
    hostel = models.ForeignKey('authentication.Hostel', on_delete=models.CASCADE, related_name='fee_structures', null=True, blank=True)
    fee_type = models.CharField(max_length=20, choices=FEE_TYPES, default='other')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    late_fee_per_day = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = ('hostel', 'fee_type')

    def __str__(self):
        return f"{self.get_fee_type_display()} - {self.amount}"


class InstallmentConfig(models.Model):
    hostel = models.ForeignKey('authentication.Hostel', on_delete=models.CASCADE, related_name='installment_configs', null=True, blank=True)
    part1_due_date = models.DateField(null=True, blank=True, verbose_name="Part 1 Due Date")
    part1_late_fee_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Part 1 Late Fee per Day")
    part2_due_date = models.DateField(null=True, blank=True, verbose_name="Part 2 Due Date")
    part2_late_fee_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Part 2 Late Fee per Day")

    class Meta:
        verbose_name = "Installment Configuration"
        verbose_name_plural = "Installment Configurations"

    def save(self, *args, **kwargs):
        if not self.hostel:
            self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls, hostel=None):
        if hostel:
            config, created = cls.objects.get_or_create(hostel=hostel)
        else:
            config, created = cls.objects.get_or_create(pk=1)
        return config



