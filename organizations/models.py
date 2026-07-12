from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.utils.functional import cached_property


class Organization(models.Model):
    """
    Level 2: An Organization (University, College, PG Company, etc.)
    sits above all Hostels. Every record in the system is scoped to one.
    """
    ORG_TYPES = [
        ('university', 'University'),
        ('college', 'College'),
        ('hostel_company', 'Hostel Management Company'),
        ('residential_campus', 'Residential Campus'),
        ('pg_company', 'PG Management Company'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    unique_code = models.CharField(max_length=50, unique=True, null=True, blank=True, help_text="Unique Organization ID / Code")
    org_type = models.CharField(max_length=30, choices=ORG_TYPES, default='university')

    # Branding / Identity
    logo = models.ImageField(upload_to='org_logos/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#6366f1', help_text='Hex color')
    secondary_color = models.CharField(max_length=7, default='#0d6efd', help_text='Hex color')

    # Contact
    address = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)

    # White-label domain
    subdomain = models.CharField(
        max_length=100, blank=True, unique=True, null=True,
        help_text='e.g. "abc" for abc.yourerp.com'
    )
    custom_domain = models.CharField(
        max_length=255, blank=True,
        help_text='e.g. hms.abcuniversity.edu'
    )

    # Locale
    timezone = models.CharField(max_length=100, default='Asia/Kolkata')
    currency = models.CharField(max_length=10, default='INR')
    language = models.CharField(max_length=10, default='en')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            n = 1
            while Organization.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{n}"
                n += 1
            self.slug = slug
        if not self.unique_code:
            import uuid
            self.unique_code = f"ORG-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @cached_property
    def hostel_count(self):
        return self.hostels.count()

    @cached_property
    def student_count(self):
        return self.students.count()

    @property
    def active_subscription(self):
        return self.subscriptions.filter(is_active=True).select_related('plan').first()


class SubscriptionPlan(models.Model):
    """Plans available for purchase by Organizations."""
    PLAN_TIERS = [
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]

    name = models.CharField(max_length=100, unique=True)
    tier = models.CharField(max_length=20, choices=PLAN_TIERS, default='basic')
    description = models.TextField(blank=True)

    # Limits
    max_hostels = models.PositiveIntegerField(default=1, help_text='0 = unlimited')
    max_students = models.PositiveIntegerField(default=100, help_text='0 = unlimited')
    max_staff = models.PositiveIntegerField(default=10, help_text='0 = unlimited')
    storage_gb = models.PositiveIntegerField(default=5)

    # Features
    has_api_access = models.BooleanField(default=False)
    has_ai_features = models.BooleanField(default=False)
    has_white_label = models.BooleanField(default=False)
    has_mobile_app = models.BooleanField(default=False)
    has_advanced_analytics = models.BooleanField(default=False)
    has_biometric_integration = models.BooleanField(default=False)
    has_rfid_support = models.BooleanField(default=False)

    # Pricing
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    annual_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['monthly_price']

    def __str__(self):
        return f"{self.name} ({self.get_tier_display()})"


class OrganizationSubscription(models.Model):
    """Links an Organization to a SubscriptionPlan with billing details."""
    PAYMENT_STATUS = [
        ('active', 'Active'),
        ('pending', 'Payment Pending'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
        ('trial', 'Trial'),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='subscriptions'
    )
    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions'
    )
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='trial')
    invoice_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.organization.name} → {self.plan.name}"

    @property
    def is_expired(self):
        if self.end_date:
            return timezone.now().date() > self.end_date
        return False


class WhiteLabelConfig(models.Model):
    """Per-organization white-label branding configuration."""
    organization = models.OneToOneField(
        Organization, on_delete=models.CASCADE, related_name='whitelabel'
    )

    # Branding
    logo = models.ImageField(upload_to='whitelabel_logos/', blank=True, null=True)
    favicon = models.ImageField(upload_to='whitelabel_favicons/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#6366f1')
    secondary_color = models.CharField(max_length=7, default='#0d6efd')
    accent_color = models.CharField(max_length=7, default='#10b981')

    # Login page
    login_background = models.ImageField(upload_to='whitelabel_bg/', blank=True, null=True)
    login_tagline = models.CharField(max_length=255, blank=True)

    # Footer / reports
    footer_text = models.CharField(max_length=255, blank=True)
    report_header = models.TextField(blank=True)
    custom_css = models.TextField(blank=True, help_text='Custom CSS injected into <head>')

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"White Label: {self.organization.name}"


class SupportTicket(models.Model):
    """Support tickets raised by organizations to Super Admin."""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    CATEGORY_CHOICES = [
        ('billing', 'Billing & Subscription'),
        ('technical', 'Technical Issue'),
        ('feature_request', 'Feature Request'),
        ('account', 'Account Management'),
        ('other', 'Other'),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='support_tickets'
    )
    raised_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='raised_tickets'
    )
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets'
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='technical')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.id} [{self.get_priority_display()}] {self.title}"


class OrganizationSettings(models.Model):
    """
    Business configuration for an Organization —
    academic years, departments, courses, fee & attendance policies.
    """
    organization = models.OneToOneField(
        Organization, on_delete=models.CASCADE, related_name='settings'
    )

    # Academic
    current_academic_year = models.CharField(max_length=20, default='2025-26')
    academic_years = models.JSONField(default=list, blank=True)
    departments = models.JSONField(default=list, blank=True)
    courses = models.JSONField(default=list, blank=True)

    # Policies (plain text / markdown)
    fee_policy = models.TextField(blank=True)
    attendance_policy = models.TextField(blank=True)
    visitor_policy = models.TextField(blank=True)
    leave_policy = models.TextField(blank=True)
    hostel_rules = models.TextField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings: {self.organization.name}"
