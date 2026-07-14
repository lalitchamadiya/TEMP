from django import forms
from .models import Room, Floor, HostelBuilding, ROOM_TYPE_CHOICES, ROOM_CATEGORY_CHOICES, ROOM_STATUS_CHOICES, GENDER_CHOICES, BLOCK_CHOICES, CAPACITY_MAP


class CreateRoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            'building', 'block', 'floor',
            'room_number', 'room_name',
            'room_type', 'category',
            'capacity', 'is_ac',
            'status', 'monthly_rent', 'description',
        ]
        widgets = {
            'building': forms.Select(attrs={
                'class': 'form-select rounded-3 shadow-none',
                'id': 'id_building',
            }),
            'block': forms.Select(attrs={
                'class': 'form-select rounded-3 shadow-none',
            }),
            'floor': forms.Select(attrs={
                'class': 'form-select rounded-3 shadow-none',
                'id': 'id_floor',
            }),
            'room_number': forms.TextInput(attrs={
                'class': 'form-control rounded-3 shadow-none',
                'placeholder': 'e.g. 101, A-201',
                'id': 'id_room_number',
                'autocomplete': 'off',
            }),
            'room_name': forms.TextInput(attrs={
                'class': 'form-control rounded-3 shadow-none',
                'placeholder': 'Optional friendly name',
            }),
            'room_type': forms.Select(attrs={
                'class': 'form-select rounded-3 shadow-none',
                'id': 'id_room_type',
            }),
            'category': forms.Select(attrs={
                'class': 'form-select rounded-3 shadow-none',
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control rounded-3 shadow-none',
                'min': 1, 'max': 50,
                'id': 'id_capacity',
            }),
            'is_ac': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select rounded-3 shadow-none',
            }),
            'monthly_rent': forms.NumberInput(attrs={
                'class': 'form-control rounded-3 shadow-none',
                'placeholder': '0.00',
                'step': '0.01',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control rounded-3 shadow-none',
                'rows': 3,
                'placeholder': 'Optional notes or description…',
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        hostel = kwargs.pop('hostel', None)
        super().__init__(*args, **kwargs)
        building_qs = HostelBuilding.objects.filter(is_active=True)
        if hostel:
            building_qs = building_qs.filter(hostel=hostel)
        self.fields['building'].queryset = building_qs
        self.fields['building'].empty_label = '— Select Building —'
        self.fields['floor'].empty_label = '— Select Floor —'
        self.fields['block'].required = False
        self.fields['room_name'].required = False
        self.fields['description'].required = False
        self.fields['monthly_rent'].required = False

        # Dynamically set choices based on active pricing configurations
        from room.models import RoomTypePricing, RoomCategoryPricing
        from django.db.models import Q
        
        pricing_q = Q(hostel=hostel) if hostel else Q(hostel__isnull=True)
        
        rtc = [('CUSTOM', 'Custom')]
        rtp_qs = RoomTypePricing.objects.filter(pricing_q, is_active=True)
        if hostel and not rtp_qs.exists():
            rtp_qs = RoomTypePricing.objects.filter(hostel__isnull=True, is_active=True)
        for rtp in rtp_qs:
            rtc.append((rtp.room_type, rtp.label or rtp.room_type))
        
        if self.instance and self.instance.pk and self.instance.room_type not in [x[0] for x in rtc]:
            rtc.append((self.instance.room_type, self.instance.room_type))
        self.fields['room_type'].choices = rtc

        rcc = []
        rcp_qs = RoomCategoryPricing.objects.filter(pricing_q, is_active=True)
        if hostel and not rcp_qs.exists():
            rcp_qs = RoomCategoryPricing.objects.filter(hostel__isnull=True, is_active=True)
        for rcp in rcp_qs:
            rcc.append((rcp.category, rcp.label or rcp.category))
            
        if self.instance and self.instance.pk and self.instance.category not in [x[0] for x in rcc]:
            rcc.append((self.instance.category, self.instance.category))
        self.fields['category'].choices = rcc

    def clean_room_number(self):
        number = self.cleaned_data.get('room_number', '').strip()
        if not number:
            raise forms.ValidationError("Room number is required.")
        building = self.cleaned_data.get('building')
        if building:
            qs = Room.objects.filter(room_number__iexact=number, building=building)
        else:
            qs = Room.objects.filter(room_number__iexact=number)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f"Room '{number}' already exists.")
        return number

    def clean_capacity(self):
        cap = self.cleaned_data.get('capacity')
        if cap is None or cap < 1:
            raise forms.ValidationError("Capacity must be at least 1.")
        return cap


# Legacy form kept for backward compat
class CreateRoom(forms.ModelForm):
    class Meta:
        model = Room
        fields = ('room_number', 'room_type', 'gender')
        widgets = {
            'room_number': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Enter room number'}),
            'room_type': forms.Select(attrs={'class': 'form-control form-control-sm select'}),
            'gender': forms.Select(attrs={'class': 'form-control form-control-sm select'}),
        }


class HostelBuildingForm(forms.ModelForm):
    class Meta:
        model = HostelBuilding
        fields = ['name', 'description', 'gender', 'total_floors', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control rounded-3 shadow-none',
                'placeholder': 'e.g. Block A, North Wing',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control rounded-3 shadow-none',
                'rows': 3,
                'placeholder': 'Optional description…',
            }),
            'gender': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none'}),
            'total_floors': forms.NumberInput(attrs={
                'class': 'form-control rounded-3 shadow-none',
                'min': 0, 'max': 50,
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch',
            }),
        }