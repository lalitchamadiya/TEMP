from django import forms
from fees.models import FeeStructure, FeeComponent, FeeCategory, FeeDiscountRule, FeeFineRule
from room.models import HostelBuilding


class FeeComponentForm(forms.ModelForm):
    class Meta:
        model = FeeComponent
        fields = ['name', 'category', 'component_type', 'default_amount', 'is_mandatory', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. WiFi Charges'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'component_type': forms.Select(attrs={'class': 'form-select'}),
            'default_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = [
            'name', 'building', 'room_type', 'academic_year', 'applicable_for',
            'payment_frequency', 'due_day', 'late_fee_rule', 'late_fee_amount',
            'grace_period_days', 'allow_partial', 'max_partial_percent',
            'enable_online', 'offline_modes', 'include_gst', 'gst_percent'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2 Bed Boys Hostel 2026'}),
            'building': forms.Select(attrs={'class': 'form-select', 'id': 'id_building'}),
            'room_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_room_type'}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'applicable_for': forms.Select(attrs={'class': 'form-select'}),
            'payment_frequency': forms.Select(attrs={'class': 'form-select', 'id': 'id_payment_frequency'}),
            'due_day': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
            'late_fee_rule': forms.Select(attrs={'class': 'form-select', 'id': 'id_late_fee_rule'}),
            'late_fee_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'grace_period_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'allow_partial': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_partial_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'enable_online': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'offline_modes': forms.TextInput(attrs={'class': 'form-control'}),
            'include_gst': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_include_gst'}),
            'gst_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_gst_percent'}),
        }
