from django.test import TestCase
from .forms import StudentForm
from .models import Student
from django.contrib.auth.models import User


class StudentFormTests(TestCase):
    def test_dob_cannot_be_future(self):
        form = StudentForm(data={'email': 'a@b.com', 'dob': '2999-01-01'})
        self.assertFalse(form.is_valid())
        self.assertIn('dob', form.errors)

    def test_phone_format(self):
        form = StudentForm(data={'email': 'a@b.com', 'phone_number': '12345'})
        self.assertFalse(form.is_valid())
        self.assertIn('phone_number', form.errors)

    def test_email_uniqueness(self):
        user = User.objects.create_user(username='x@x.com', password='pwd')
        Student.objects.create(user=user, email='x@x.com', name='X')
        form = StudentForm(data={'email': 'x@x.com'})
        self.assertFalse(form.is_valid())
