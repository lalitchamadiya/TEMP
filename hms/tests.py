from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from authentication.models import AuditLog, Hostel, Role, UserProfile

class SuperAdminDashboardAuditLogTests(TestCase):
    def setUp(self):
        # Create superuser
        self.user = User.objects.create_superuser(username='superadmin', email='admin@hms.com', password='password')
        self.client = Client()
        self.client.force_login(self.user)
        
        # Setup session for active hostel
        self.hostel = Hostel.objects.create(name='Main Hostel', is_active=True)
        session = self.client.session
        session['active_hostel_id'] = self.hostel.id
        session.save()

        # Create user profile and role
        self.role = Role.objects.create(name='SuperAdmin', is_superadmin=True, is_active=True)
        self.profile = UserProfile.objects.create(user=self.user, role=self.role)

        # Create audit logs
        self.log_create = AuditLog.objects.create(
            actor=self.user,
            action='create',
            details='Test user creation logs text',
            ip_address='192.168.1.1'
        )
        self.log_edit = AuditLog.objects.create(
            actor=self.user,
            action='edit',
            details='Test user edit details contents',
            ip_address='10.0.0.1'
        )
        self.log_delete = AuditLog.objects.create(
            actor=self.user,
            action='delete',
            details='Test user deletion logging',
            ip_address='8.8.8.8'
        )

    def test_dashboard_renders_audit_logs(self):
        """Verify the superadmin dashboard opens and displays the logs."""
        response = self.client.get(reverse('superadmin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Security & Administrative Audit Logs')
        self.assertContains(response, 'Test user creation logs text')
        self.assertContains(response, 'Test user edit details contents')
        self.assertContains(response, 'Test user deletion logging')
        self.assertContains(response, '192.168.1.1')
        self.assertContains(response, '10.0.0.1')
        self.assertContains(response, '8.8.8.8')

    def test_dashboard_search_audit_logs(self):
        """Verify log_q filters the audit logs list."""
        # Search for 'creation'
        response = self.client.get(reverse('superadmin_dashboard'), {'log_q': 'creation'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test user creation logs text')
        self.assertNotContains(response, 'Test user edit details contents')
        self.assertNotContains(response, 'Test user deletion logging')

        # Search for IP '10.0.0.1'
        response = self.client.get(reverse('superadmin_dashboard'), {'log_q': '10.0.0.1'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Test user creation logs text')
        self.assertContains(response, 'Test user edit details contents')
        self.assertNotContains(response, 'Test user deletion logging')

    def test_dashboard_filter_action_audit_logs(self):
        """Verify log_action filters the audit logs list."""
        response = self.client.get(reverse('superadmin_dashboard'), {'log_action': 'delete'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Test user creation logs text')
        self.assertNotContains(response, 'Test user edit details contents')
        self.assertContains(response, 'Test user deletion logging')

    def test_dashboard_date_range_filtering_audit_logs(self):
        """Verify log_start_date and log_end_date filters the audit logs list."""
        import datetime
        from django.utils import timezone
        
        # Delete default setup logs to avoid date collision in this specific test
        AuditLog.objects.all().delete()
        
        # Create logs on specific dates
        date_old = timezone.now() - datetime.timedelta(days=5)
        date_recent = timezone.now() - datetime.timedelta(days=2)
        date_future = timezone.now() + datetime.timedelta(days=5)
        
        log1 = AuditLog.objects.create(
            actor=self.user,
            action='create',
            details='Old audit log info',
            timestamp=date_old
        )
        log2 = AuditLog.objects.create(
            actor=self.user,
            action='edit',
            details='Recent audit log info',
            timestamp=date_recent
        )
        log3 = AuditLog.objects.create(
            actor=self.user,
            action='delete',
            details='Future audit log info',
            timestamp=date_future
        )
        
        # Filter with start date = date_recent (2 days ago)
        start_str = date_recent.strftime('%Y-%m-%d')
        response = self.client.get(reverse('superadmin_dashboard'), {'log_start_date': start_str})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recent audit log info')
        self.assertContains(response, 'Future audit log info')
        self.assertNotContains(response, 'Old audit log info')
        
        # Filter with end date = date_recent
        end_str = date_recent.strftime('%Y-%m-%d')
        response = self.client.get(reverse('superadmin_dashboard'), {'log_end_date': end_str})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Future audit log info')
        self.assertContains(response, 'Recent audit log info')
        self.assertContains(response, 'Old audit log info')

    def test_dashboard_export_csv_audit_logs(self):
        """Verify downloading Audit Logs as a CSV works."""
        response = self.client.get(reverse('superadmin_dashboard'), {'log_export': 'csv', 'log_q': 'creation'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="audit_logs_export.csv"', response['Content-Disposition'])
        
        # Read the CSV content
        content = response.content.decode('utf-8')
        self.assertIn('Test user creation logs text', content)
        self.assertNotIn('Test user edit details contents', content)

    def test_dashboard_ajax_scroll_loading_audit_logs(self):
        """Verify AJAX requests return JSON with rendered rows html."""
        response = self.client.get(reverse('superadmin_dashboard'), {'ajax': '1', 'log_page': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertIn('html', data)
        self.assertIn('has_next', data)
        self.assertIn('Test user creation logs text', data['html'])

    def test_live_dashboard_stats_ajax_endpoint(self):
        """Verify the AJAX stats endpoint returns JSON with all required keys."""
        response = self.client.get(reverse('live_dashboard_stats'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertIn('total_students', data)
        self.assertIn('active_students', data)
        self.assertIn('occupied_beds', data)
        self.assertIn('monthly_revenue', data)
        self.assertIn('open_complaints', data)
        self.assertIn('disk_pct', data)


class DutyAssignmentDashboardTests(TestCase):
    def setUp(self):
        from room.models import HostelBuilding, Room, Bed
        from hms.models import StaffProfile, Duty, DutyPermission, DutyAssignment
        from student.models import Student
        from leave.models import HostelLeave

        # Create basic roles
        self.role_warden = Role.objects.create(name='Warden', is_active=True)
        self.role_sec = Role.objects.create(name='Security', is_active=True)

        # Create users
        self.warden_user = User.objects.create_user(username='test_warden', email='warden@hms.com', password='password')
        self.sec_user = User.objects.create_user(username='test_sec', email='sec@hms.com', password='password')

        # Create UserProfiles
        self.warden_prof = UserProfile.objects.create(user=self.warden_user, role=self.role_warden)
        self.sec_prof = UserProfile.objects.create(user=self.sec_user, role=self.role_sec)

        # Create StaffProfiles with mandatory fields
        self.warden_staff = StaffProfile.objects.create(
            user=self.warden_user,
            name='Test Warden Staff',
            email='warden_staff@hms.com',
            phone='1234567890',
            designation='warden'
        )
        self.sec_staff = StaffProfile.objects.create(
            user=self.sec_user,
            name='Test Sec Staff',
            email='sec_staff@hms.com',
            phone='0987654321',
            designation='guard'
        )

        # Setup Building layout
        self.building_a = HostelBuilding.objects.create(name='Building A')
        self.building_b = HostelBuilding.objects.create(name='Building B')

        self.room_a = Room.objects.create(room_number='101', building=self.building_a, floor=1)
        self.room_b = Room.objects.create(room_number='201', building=self.building_b, floor=1)

        self.bed_a = Bed.objects.create(bed_number='101-A', room=self.room_a)
        self.bed_b = Bed.objects.create(bed_number='201-A', room=self.room_b)

        # Create test students
        self.student_a = Student.objects.create(name='Student A', email='student_a@hms.com', roll='123456', status='Active')
        self.student_b = Student.objects.create(name='Student B', email='student_b@hms.com', roll='789012', status='Active')

        # Allocate beds
        self.bed_a.student = self.student_a
        self.bed_a.save()
        self.bed_b.student = self.student_b
        self.bed_b.save()

        # Create duties
        self.duty_warden = Duty.objects.create(name='Warden Duty', category='warden', priority='High', status='active')
        self.duty_sec = Duty.objects.create(name='Gate Duty', category='security', priority='Medium', status='active')

        # Create duty permissions
        # Warden Duty can view and add student records, but no leaves or fees
        DutyPermission.objects.create(duty=self.duty_warden, module_name='students', can_view=True, can_add=True)
        # Sec Duty can view leaves only
        DutyPermission.objects.create(duty=self.duty_sec, module_name='leave', can_view=True)

        # Create Duty Assignments
        # Warden assigned to Building A only
        self.assign_warden = DutyAssignment.objects.create(
            staff=self.warden_staff,
            duty=self.duty_warden,
            duty_title='Warden Duty',
            specific_location='Building A',
            is_active=True
        )
        # Security assigned to Building B only
        self.assign_sec = DutyAssignment.objects.create(
            staff=self.sec_staff,
            duty=self.duty_sec,
            duty_title='Gate Duty',
            specific_location='Building B',
            is_active=True
        )

        # Create leave pass
        import datetime
        from django.utils import timezone
        today_date = timezone.now().date()
        self.leave_a = HostelLeave.objects.create(student=self.student_a, status='approved', exit_verified=False, leave_from=today_date)
        self.leave_b = HostelLeave.objects.create(student=self.student_b, status='approved', exit_verified=False, leave_from=today_date)

    def test_rbac_context_override_for_active_duty(self):
        """Verify rbac_context filters allowed modules based on the active duty permissions."""
        from authentication.context_processors import rbac_context
        from django.test import RequestFactory

        # Test for Warden (should have student view/add, but not leave)
        request = RequestFactory().get('/')
        request.user = self.warden_user
        context = rbac_context(request)

        perms = context['user_permissions']
        self.assertTrue(perms.get('student', {}).get('view'))
        self.assertTrue(perms.get('student', {}).get('add'))
        self.assertFalse(perms.get('leave', {}).get('view'))

        # Test for Security (should have leave view, but not student)
        request2 = RequestFactory().get('/')
        request2.user = self.sec_user
        context2 = rbac_context(request2)

        perms2 = context2['user_permissions']
        self.assertFalse(perms2.get('student', {}).get('view'))
        self.assertTrue(perms2.get('leave', {}).get('view'))

    def test_warden_dashboard_location_scoping(self):
        """Verify warden dashboard queries only return students within assigned Location scope."""
        self.client.force_login(self.warden_user)
        response = self.client.get(reverse('warden_dashboard'))
        self.assertEqual(response.status_code, 200)

        # Warden is assigned to Building A (Student A is in Building A, Student B is in Building B)
        # The list should contain Student A, but NOT Student B
        recent_students = response.context['recent_students']
        student_ids = [s.student_id for s in recent_students]
        self.assertIn(self.student_a.student_id, student_ids)
        self.assertNotIn(self.student_b.student_id, student_ids)

    def test_security_dashboard_location_scoping(self):
        """Verify security dashboard queries only return leaves within assigned Location scope."""
        self.client.force_login(self.sec_user)
        # Mock view permission requirement checks via context processor overrides
        response = self.client.get(reverse('security_dashboard'))
        self.assertEqual(response.status_code, 200)

        # Security is assigned to Building B (Student B is in Building B)
        # pending_exits must filter out self.leave_a (which is Building A)
        pending_exits = response.context['pending_exits']
        leave_ids = [l.id for l in pending_exits]
        self.assertIn(self.leave_b.id, leave_ids)
        self.assertNotIn(self.leave_a.id, leave_ids)


