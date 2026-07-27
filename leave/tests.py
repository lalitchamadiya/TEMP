from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date, time
from student.models import Student
from leave.models import HostelLeave, QRPass, GatePass

class LeaveGatingTestCase(TestCase):
    def setUp(self):
        # Create a user and student
        self.user = User.objects.create_user(username='student_test', email='student@test.com', password='password123')
        self.superuser = User.objects.create_superuser(username='admin_test', email='admin@test.com', password='password123')
        
        self.student = Student.objects.create(
            user=self.user,
            name='Test Student',
            roll='ROLL123',
            email='student@test.com',
            phone_number='1234567890',
            gender='Male',
            academic_year='1st Year',
            status='Active'
        )
        
        # Create a leave request
        self.leave = HostelLeave.objects.create(
            student=self.student,
            leave_from=date.today(),
            leave_to=date.today() + timedelta(days=2),
            start_time=time(10, 0),
            end_time=time(17, 0),
            reason='Medical Checkup',
            status='pending'
        )
        
        # Setup clients
        self.client = Client()
        self.client.login(username='admin_test', password='password123')

    def test_leave_approval_generates_exit_pass(self):
        # Approve the leave through view logic or utility
        from leave.views import process_leave_action
        
        # Mock request with superuser
        class MockRequest:
            user = self.superuser
            META = {'REMOTE_ADDR': '127.0.0.1'}
            
        process_leave_action(MockRequest(), self.leave, 'approve')
        
        # Check that HostelLeave status is 'approved'
        self.leave.refresh_from_db()
        self.assertEqual(self.leave.status, 'approved')
        
        # Check that an EXIT QRPass was automatically created
        exit_pass = QRPass.objects.filter(leave=self.leave, pass_type='EXIT').first()
        self.assertIsNotNone(exit_pass)
        self.assertFalse(exit_pass.is_used)
        self.assertEqual(exit_pass.expires_at.date(), self.leave.leave_from)
        
        # Check that student status remains Active on leave approval
        self.student.refresh_from_db()
        self.assertEqual(self.student.status, 'Active')

    def test_qr_code_image_view(self):
        # Generate EXIT pass
        expires_at = timezone.make_aware(timezone.datetime.combine(self.leave.leave_from, time(23, 59, 59)))
        exit_pass = QRPass.objects.create(
            leave=self.leave,
            pass_type='EXIT',
            expires_at=expires_at
        )
        url = reverse('qr_code_image', kwargs={'qr_token': exit_pass.qr_token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'image/png')
        self.assertTrue(len(response.content) > 0)

    def test_exit_pass_verification_flow(self):
        # Generate EXIT pass
        expires_at = timezone.make_aware(timezone.datetime.combine(self.leave.leave_from, time(23, 59, 59)))
        exit_pass = QRPass.objects.create(
            leave=self.leave,
            pass_type='EXIT',
            expires_at=expires_at
        )
        
        # Status needs to be approved for scan execution
        self.leave.status = 'approved'
        self.leave.save()
        
        # Perform POST to scan endpoint to approve exit
        url = reverse('scan_gate_pass', kwargs={'qr_token': exit_pass.qr_token})
        response = self.client.post(url)
        
        # Verify redirect or success render
        self.assertEqual(response.status_code, 200)
        
        # Verify leave and student state changes
        self.leave.refresh_from_db()
        self.student.refresh_from_db()
        exit_pass.refresh_from_db()
        
        self.assertTrue(self.leave.exit_verified)
        self.assertIsNotNone(self.leave.exit_time)
        self.assertTrue(exit_pass.is_used)
        self.assertEqual(self.student.status, 'On Leave')
        
        # Verify an ENTRY pass gets created
        entry_pass = QRPass.objects.filter(leave=self.leave, pass_type='ENTRY').first()
        self.assertIsNotNone(entry_pass)
        self.assertFalse(entry_pass.is_used)

    def test_entry_pass_verification_flow(self):
        # Setup student as outside (exited)
        self.leave.status = 'approved'
        self.leave.exit_verified = True
        self.leave.exit_time = timezone.now() - timedelta(hours=5)
        self.leave.save()
        
        self.student.status = 'On Leave'
        self.student.save()
        
        # Create ENTRY pass
        expires_at = timezone.make_aware(timezone.datetime.combine(self.leave.leave_to, time(23, 59, 59)))
        entry_pass = QRPass.objects.create(
            leave=self.leave,
            pass_type='ENTRY',
            expires_at=expires_at
        )
        
        # Perform POST to scan endpoint to approve entry
        url = reverse('scan_gate_pass', kwargs={'qr_token': entry_pass.qr_token})
        response = self.client.post(url)
        
        # Verify OK
        self.assertEqual(response.status_code, 200)
        
        # Verify leave and student state changes
        self.leave.refresh_from_db()
        self.student.refresh_from_db()
        entry_pass.refresh_from_db()
        
        self.assertTrue(self.leave.entry_verified)
        self.assertIsNotNone(self.leave.entry_time)
        self.assertEqual(self.leave.status, 'completed')
        self.assertTrue(entry_pass.is_used)
        self.assertEqual(self.student.status, 'Active')

    def test_used_pass_validation_error(self):
        # Create used pass
        expires_at = timezone.now() + timedelta(hours=2)
        used_pass = QRPass.objects.create(
            leave=self.leave,
            pass_type='EXIT',
            expires_at=expires_at,
            is_used=True,
            used_at=timezone.now()
        )
        
        self.leave.status = 'approved'
        self.leave.save()
        
        # Try to scan/POST
        url = reverse('scan_gate_pass', kwargs={'qr_token': used_pass.qr_token})
        response = self.client.post(url)
        
        # Check for error in response context
        self.assertEqual(response.context['error_msg'], "Pass Already Used")

    def test_cancel_gate_pass(self):
        self.leave.status = 'approved'
        self.leave.save()
        gp = GatePass.objects.create(gate_pass_no='GP-12345', leave_request=self.leave)
        
        # Create an active QRPass
        qr = QRPass.objects.create(
            leave=self.leave,
            pass_type='EXIT',
            expires_at=timezone.now() + timedelta(days=1)
        )
        
        url = reverse('cancel_gate_pass', kwargs={'gp_id': gp.id})
        response = self.client.post(url)
        
        # Verify redirect
        self.assertRedirects(response, reverse('gate_pass_management'))
        
        # Verify status changes
        gp.refresh_from_db()
        self.leave.refresh_from_db()
        qr.refresh_from_db()
        
        self.assertEqual(gp.status, 'Cancelled')
        self.assertEqual(self.leave.status, 'rejected')
        self.assertTrue(qr.is_used)
