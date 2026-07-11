from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import datetime
import re

from .models import Student, GENDER_CHOICES, STATE_CHOICES, COURSE_CHOICES, SEM_CHOICES, CITY_CHOICES


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'photo', 'name', 'roll', 'email', 'phone_number', 'gender', 'dob',
            'blood_group', 'category', 'nationality',
            'father_name', 'mother_name', 'guardian_name', 'guardian_phone',
            'guardian_occupation', 'parent_email',
            'course', 'department', 'semester', 'division',
            'admission_date', 'admission_number', 'academic_year', 'status',
            'address', 'address_line_2', 'state', 'city', 'country', 'pincode',
            'emergency_name', 'emergency_relation', 'emergency_phone', 'emergency_alt_phone',
        ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'admission_date': forms.DateInput(attrs={'type': 'date'}),
            'status': forms.Select(),
            'gender': forms.Select(),
            'blood_group': forms.Select(),
            'category': forms.Select(),
            'nationality': forms.Select(),
            'division': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Add premium styling classes
            existing_classes = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = f'{existing_classes} form-check-input'.strip()
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = f'{existing_classes} form-select rounded-3 shadow-none'.strip()
            else:
                field.widget.attrs['class'] = f'{existing_classes} form-control rounded-3 shadow-none'.strip()
            
            # Placeholder for better UX
            field.widget.attrs.setdefault('placeholder', f'Enter {field.label}')

    def clean_dob(self):
        dob = self.cleaned_data.get('dob')
        if dob and dob > datetime.date.today():
            raise ValidationError("Date of birth cannot be in the future.")
        return dob

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email
        qs = Student.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Email is already used by another student.")
        user_qs = User.objects.filter(email=email)
        if self.instance.pk and self.instance.user:
            user_qs = user_qs.exclude(pk=self.instance.user.pk)
        if user_qs.exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_roll(self):
        roll = self.cleaned_data.get('roll')
        if not roll:
            return roll
        qs = Student.objects.filter(roll=roll)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Enrollment Number (Roll) is already used by another student.")
        user_qs = User.objects.filter(username=roll)
        if self.instance.pk and self.instance.user:
            user_qs = user_qs.exclude(pk=self.instance.user.pk)
        if user_qs.exists():
            raise ValidationError("A user with this Enrollment Number as username already exists.")
        return roll

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            pattern = r'^\+\d{1,3}\d{7,12}$'
            if not re.match(pattern, phone):
                raise ValidationError(
                    "Enter phone number in international format e.g. +1234567890"
                )
        return phone


class StudentSelfUpdateForm(StudentForm):
    class Meta(StudentForm.Meta):
        fields = [
            'photo', 'phone_number', 'blood_group',
            'father_name', 'mother_name', 'guardian_name', 'guardian_phone',
            'guardian_occupation', 'parent_email',
            'address', 'address_line_2', 'state', 'city', 'country', 'pincode',
            'emergency_name', 'emergency_relation', 'emergency_phone', 'emergency_alt_phone',
        ]