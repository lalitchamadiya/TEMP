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


from django.core.files.uploadedfile import SimpleUploadedFile

class StudentProfileViewAndSessionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='student_prof', password='password123', email='prof@example.com')
        from authentication.models import Role, UserProfile
        self.role, _ = Role.objects.get_or_create(name='Student')
        self.profile = UserProfile.objects.create(user=self.user, role=self.role)
        self.student = Student.objects.create(
            user=self.user,
            name='Profile Student',
            roll='2002',
            email='prof@example.com'
        )

    def test_student_profile_view_accessible(self):
        self.client.login(username='student_prof', password='password123')
        url = reverse('student_app:student_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Profile Student')
        self.assertContains(response, '2002')

    def test_student_profile_update_photo_and_session_persistence(self):
        self.client.login(username='student_prof', password='password123')
        update_url = reverse('student_app:student_profile_update')

        # Dummy image for upload
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
            b'\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
            b'\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        )
        uploaded_photo = SimpleUploadedFile('test_photo.gif', small_gif, content_type='image/gif')

        post_data = {
            'phone_number': '9876543210',
            'blood_group': 'O+',
            'photo': uploaded_photo,
        }

        response = self.client.post(update_url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Refresh student model from DB
        self.student.refresh_from_db()
        self.assertTrue(bool(self.student.photo))
        self.assertIn('test_photo', self.student.photo.name)

        # Verify profile view shows photo URL
        profile_url = reverse('student_app:student_profile')
        profile_response = self.client.get(profile_url)
        self.assertEqual(profile_response.status_code, 200)
        self.assertContains(profile_response, self.student.photo.url)

