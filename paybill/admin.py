from django.contrib import admin
from .models import Payment, FeeStructure, GatewayConfig

@admin.register(GatewayConfig)
class GatewayConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'is_live')
    list_filter = ('is_active', 'is_live')
    search_fields = ('name',)

from django.utils.html import format_html
from django.urls import reverse

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'student', 'amount', 'transaction_status', 'payment_type', 'gateway_name', 'created_at', 'receipt_link')
    list_filter = ('transaction_status', 'payment_type', 'gateway_name', 'created_at')
    search_fields = ('transaction_id', 'enrollment_number', 'user_name', 'student__name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    actions = ['issue_refund']

    def receipt_link(self, obj):
        if obj.transaction_status == 'SUCCESSFUL':
            url = reverse('student_app:fee_receipt', args=[obj.transaction_id])
            return format_html('<a href="{}" target="_blank">View Receipt</a>', url)
        return "-"
    receipt_link.short_description = "Receipt"

    @admin.action(description="Issue Refund for selected payments")
    def issue_refund(self, request, queryset):
        success_count = 0
        for payment in queryset:
            if payment.transaction_status == 'SUCCESSFUL':
                # In a real scenario, call the gateway refund API here
                payment.transaction_status = 'REFUNDED'
                payment.save()
                success_count += 1
        self.message_user(request, f"Successfully refunded {success_count} payments.")

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('fee_type', 'amount', 'due_date', 'late_fee_per_day')
    list_filter = ('fee_type',)
    search_fields = ('fee_type',)
