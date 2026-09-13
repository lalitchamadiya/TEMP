from django.test import TestCase
from .forms import StudentForm
from .models import Student
from django.contrib.auth.models import User


class StudentFormTests(TestCase):
    def test_dob_cannot_be_future(self):
        form = StudentForm(data={'email': 'a@b.com', 'dob': '2999-01-01'})
        self.assertFalse(form.is_valid())
        self.assertIn('dob', form.errors)

    def test_phone_format_invalid(self):
        form = StudentForm(data={'email': 'a@b.com', 'phone_number': '12345'})
        self.assertFalse(form.is_valid())
        self.assertIn('phone_number', form.errors)

    def test_phone_auto_prefix_91(self):
        form = StudentForm(data={'phone_number': '9327431562'})
        form.is_valid()
        self.assertEqual(form.cleaned_data.get('phone_number'), '+919327431562')

    def test_student_model_phone_save_normalization(self):
        student = Student.objects.create(
            name='Test Student',
            email='testphone@example.com',
            phone_number='9876543210',
            guardian_phone='09876543210'
        )
        self.assertEqual(student.phone_number, '+919876543210')
        self.assertEqual(student.guardian_phone, '+919876543210')

    def test_email_uniqueness(self):
        user = User.objects.create_user(username='x@x.com', password='pwd')
        Student.objects.create(user=user, email='x@x.com', name='X')
        form = StudentForm(data={'email': 'x@x.com'})
        self.assertFalse(form.is_valid())
