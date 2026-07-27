from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from student.models import Student
from leave.models import HostelLeave, QRPass
from django.utils import timezone
from datetime import timedelta

class StudentActivePassStatusTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='student1', password='password123', email='student1@example.com')
        from authentication.models import Role, UserProfile
        self.role, _ = Role.objects.get_or_create(name='Student')
        self.profile = UserProfile.objects.create(user=self.user, role=self.role)
        self.student = Student.objects.create(
            user=self.user,
            name='Test Student',
            roll='1001',
            email='student1@example.com'
        )
        self.leave = HostelLeave.objects.create(
            student=self.student,
            leave_from=timezone.now().date(),
            leave_to=(timezone.now() + timedelta(days=2)).date(),
            reason='Medical',
            status='approved'
        )

    def test_active_pass_status_anonymous(self):
        url = reverse('student_app:active_pass_status', kwargs={'leave_id': self.leave.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_active_pass_status_authenticated_no_pass(self):
        self.client.login(username='student1', password='password123')
        url = reverse('student_app:active_pass_status', kwargs={'leave_id': self.leave.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['has_pass'])
        self.assertEqual(data['leave_status'], 'approved')

    def test_active_pass_status_authenticated_with_pass(self):
        self.client.login(username='student1', password='password123')
        qr = QRPass.objects.create(
            leave=self.leave,
            pass_type='EXIT',
            expires_at=timezone.now() + timedelta(hours=2)
        )
        url = reverse('student_app:active_pass_status', kwargs={'leave_id': self.leave.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['has_pass'])
        self.assertEqual(data['pass_type'], 'EXIT')
        self.assertFalse(data['is_used'])
        self.assertEqual(data['qr_token'], str(qr.qr_token))
