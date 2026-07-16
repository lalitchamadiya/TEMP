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

