from django.contrib import admin
from .models import (
    Organization, SubscriptionPlan, OrganizationSubscription,
    WhiteLabelConfig, SupportTicket, OrganizationSettings
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'org_type', 'subdomain', 'is_active', 'created_at']
    list_filter = ['org_type', 'is_active']
    search_fields = ['name', 'subdomain', 'contact_email']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'tier', 'max_hostels', 'max_students', 'monthly_price', 'is_active']
    list_filter = ['tier', 'is_active']


@admin.register(OrganizationSubscription)
class OrganizationSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['organization', 'plan', 'start_date', 'end_date', 'is_active', 'payment_status']
    list_filter = ['is_active', 'payment_status']
    search_fields = ['organization__name']


@admin.register(WhiteLabelConfig)
class WhiteLabelConfigAdmin(admin.ModelAdmin):
    list_display = ['organization', 'primary_color', 'updated_at']


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'organization', 'title', 'priority', 'status', 'created_at']
    list_filter = ['priority', 'status', 'category']
    search_fields = ['title', 'organization__name']


@admin.register(OrganizationSettings)
class OrganizationSettingsAdmin(admin.ModelAdmin):
    list_display = ['organization', 'current_academic_year', 'updated_at']
