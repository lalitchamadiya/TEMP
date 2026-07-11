from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone


class Module(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.SlugField(max_length=100, unique=True)  # e.g. 'student', 'room', 'paybill'

    # Sidebar / navigation metadata
    menu_label = models.CharField(max_length=100, blank=True, help_text="Label shown in sidebar menu")
    icon = models.CharField(max_length=60, blank=True, help_text="Bootstrap icon class e.g. bi-people")
    url_name = models.CharField(max_length=100, blank=True, help_text="Django URL name for the module index page")
    order = models.PositiveSmallIntegerField(default=0, help_text="Sidebar display order (lower = higher)")
    parent_code = models.SlugField(max_length=100, blank=True, help_text="Parent module code for sub-menus")

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_superadmin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)

    can_view = models.BooleanField(default=False)
    can_add = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_approve = models.BooleanField(default=False)
    can_reject = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)
    can_print = models.BooleanField(default=False)
    can_import = models.BooleanField(default=False)
    can_hide = models.BooleanField(default=False)
    can_disable = models.BooleanField(default=False)

    class Meta:
        unique_together = ('role', 'module')

    def __str__(self):
        return f"{self.role.name} - {self.module.name}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

    # Extended fields for User Management
    phone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to='user_photos/', blank=True, null=True)
    is_locked = models.BooleanField(default=False)  # Locked accounts cannot log in

    def __str__(self):
        return f"{self.user.username} - {self.role.name if self.role else 'No Role'}"

    @property
    def display_name(self):
        full = self.user.get_full_name()
        return full if full else self.user.username


class WardenProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='warden_profile')
    assigned_blocks = models.ManyToManyField('room.HostelBlock', blank=True)

    def __str__(self):
        return f"Warden: {self.user.username}"


class AuditLog(models.Model):
    """Records every significant administrative action for accountability."""

    ACTION_CHOICES = [
        ('create', 'User Created'),
        ('edit', 'User Edited'),
        ('delete', 'User Deleted'),
        ('activate', 'User Activated'),
        ('deactivate', 'User Deactivated'),
        ('lock', 'User Locked'),
        ('unlock', 'User Unlocked'),
        ('role_change', 'Role Changed'),
        ('password_reset', 'Password Reset'),
        ('export', 'Data Exported'),
        ('login', 'User Logged In'),
        ('logout', 'User Logged Out'),
        ('gate_pass', 'Gate Pass Action'),
    ]

    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='audit_actions', verbose_name='Performed By'
    )
    target_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_records', verbose_name='Affected User'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.actor} → {self.action} on {self.target_user}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:20]}"
