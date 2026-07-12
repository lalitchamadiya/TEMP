from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from authentication.models import Role, UserProfile
from organizations.models import (
    Organization, SubscriptionPlan, OrganizationSubscription,
    WhiteLabelConfig, SupportTicket, OrganizationSettings
)


class OrganizationFeatureTests(TestCase):
    def setUp(self):
        # 1. Create permissions structure
        self.superadmin_role = Role.objects.create(name='Super Admin', is_superadmin=True)
        self.normal_role = Role.objects.create(name='Warden', is_superadmin=False)

        # 2. Create users
        self.superadmin_user = User.objects.create_user(username='superadmin', password='Password123')
        self.superadmin_profile = UserProfile.objects.create(user=self.superadmin_user, role=self.superadmin_role)

        self.normal_user = User.objects.create_user(username='normaluser', password='Password123')
        self.normal_profile = UserProfile.objects.create(user=self.normal_user, role=self.normal_role)

        # 3. Create dummy data
        self.org = Organization.objects.create(
            name="Alpha University",
            slug="alpha-university",
            org_type="university",
            subdomain="alpha",
            is_active=True
        )
        self.plan = SubscriptionPlan.objects.create(
            name="Gold Plan",
            tier="professional",
            max_hostels=5,
            max_students=500,
            max_staff=20,
            monthly_price=99.99,
            is_active=True
        )

    # ── ACCESS CONTROL TESTS ──────────────────────────────────────────────────
    def test_anonymous_access_redirects_to_login(self):
        response = self.client.get(reverse('org_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_normal_user_denied_access(self):
        self.client.login(username='normaluser', password='Password123')
        response = self.client.get(reverse('org_list'))
        self.assertEqual(response.status_code, 403)  # PermissionDenied

    # ── ORGANIZATION CRUD TESTS ───────────────────────────────────────────────
    def test_org_list_view(self):
        self.client.login(username='superadmin', password='Password123')
        response = self.client.get(reverse('org_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha University")

    def test_org_create(self):
        self.client.login(username='superadmin', password='Password123')
        data = {
            'name': 'Beta College',
            'org_type': 'college',
            'subdomain': 'beta',
            'address': '123 College St',
            'contact_email': 'beta@college.edu',
            'contact_phone': '9999999999',
            'website': 'https://beta.edu',
            'custom_domain': 'hms.beta.edu',
            'timezone': 'Asia/Kolkata',
            'currency': 'INR',
            'language': 'en',
            'primary_color': '#6366f1',
            'secondary_color': '#0d6efd',
            'is_active': 'on',
        }
        response = self.client.post(reverse('org_create'), data=data)
        self.assertRedirects(response, reverse('org_list'))
        self.assertTrue(Organization.objects.filter(name='Beta College').exists())
        
        # Verify settings and whitelabel configuration auto-creation
        org = Organization.objects.get(name='Beta College')
        self.assertTrue(OrganizationSettings.objects.filter(organization=org).exists())
        self.assertTrue(WhiteLabelConfig.objects.filter(organization=org).exists())

    def test_org_edit(self):
        self.client.login(username='superadmin', password='Password123')
        data = {
            'name': 'Alpha University (Updated Name)',
            'org_type': 'university',
            'subdomain': 'alpha',
            'address': 'Update Addr',
            'contact_email': 'alpha-update@univ.edu',
            'timezone': 'Asia/Kolkata',
            'currency': 'INR',
            'language': 'en',
            'primary_color': '#6366f1',
            'secondary_color': '#0d6efd',
            'is_active': 'on',
        }
        response = self.client.post(reverse('org_edit', args=[self.org.pk]), data=data)
        self.assertRedirects(response, reverse('org_list'))
        self.org.refresh_from_db()
        self.assertEqual(self.org.name, 'Alpha University (Updated Name)')

    def test_org_toggle_status(self):
        self.client.login(username='superadmin', password='Password123')
        response = self.client.post(reverse('org_toggle_status', args=[self.org.pk]))
        self.assertRedirects(response, reverse('org_list'))
        self.org.refresh_from_db()
        self.assertFalse(self.org.is_active)

    def test_org_delete(self):
        self.client.login(username='superadmin', password='Password123')
        response = self.client.post(reverse('org_delete', args=[self.org.pk]))
        self.assertRedirects(response, reverse('org_list'))
        self.assertFalse(Organization.objects.filter(pk=self.org.pk).exists())

    # ── PLANS & SUBSCRIPTIONS TESTS ───────────────────────────────────────────
    def test_plan_create(self):
        self.client.login(username='superadmin', password='Password123')
        data = {
            'name': 'Pro Plan Unlimited',
            'tier': 'professional',
            'description': 'Advanced access',
            'max_hostels': 10,
            'max_students': 1000,
            'max_staff': 50,
            'storage_gb': 10,
            'monthly_price': 149.99,
            'annual_price': 1499.99,
            'is_active': 'on',
        }
        response = self.client.post(reverse('plan_create'), data=data)
        self.assertRedirects(response, reverse('plan_list'))
        self.assertTrue(SubscriptionPlan.objects.filter(name='Pro Plan Unlimited').exists())

    def test_assign_subscription(self):
        self.client.login(username='superadmin', password='Password123')
        data = {
            'organization': self.org.pk,
            'plan': self.plan.pk,
            'start_date': '2026-01-01',
            'end_date': '2027-01-01',
            'payment_status': 'active',
            'notes': 'Test assign',
        }
        response = self.client.post(reverse('assign_subscription'), data=data)
        self.assertRedirects(response, reverse('subscription_list'))
        self.assertTrue(OrganizationSubscription.objects.filter(organization=self.org, plan=self.plan).exists())

    # ── SETTINGS & WHITELABEL TESTS ───────────────────────────────────────────
    def test_org_settings_update(self):
        self.client.login(username='superadmin', password='Password123')
        settings_obj, _ = OrganizationSettings.objects.get_or_create(organization=self.org)
        data = {
            'current_academic_year': '2026-27',
            'fee_policy': 'No refund policy',
            'attendance_policy': '75% attendance mandatory',
            'visitor_policy': 'Visitor rules',
            'leave_policy': 'Warden approval required',
            'hostel_rules': 'No noise after 10PM',
            'departments': "CS\nIT\nEC",
            'courses': "B.Tech\nM.Tech",
            'academic_years': "2025-26\n2026-27",
        }
        response = self.client.post(reverse('org_settings', args=[self.org.pk]), data=data)
        self.assertRedirects(response, reverse('org_detail', args=[self.org.pk]))
        settings_obj.refresh_from_db()
        self.assertEqual(settings_obj.current_academic_year, '2026-27')
        self.assertIn("CS", settings_obj.departments)
        self.assertIn("B.Tech", settings_obj.courses)

    def test_whitelabel_config_update(self):
        self.client.login(username='superadmin', password='Password123')
        config_obj, _ = WhiteLabelConfig.objects.get_or_create(organization=self.org)
        data = {
            'primary_color': '#ff0000',
            'secondary_color': '#00ff00',
            'accent_color': '#0000ff',
            'login_tagline': 'Welcome Alpha!',
            'footer_text': 'Alpha footer',
            'report_header': 'Alpha Report',
            'custom_css': '.body { background: #000; }',
        }
        response = self.client.post(reverse('whitelabel_config', args=[self.org.pk]), data=data)
        self.assertRedirects(response, reverse('org_detail', args=[self.org.pk]))
        config_obj.refresh_from_db()
        self.assertEqual(config_obj.primary_color, '#ff0000')
        self.assertEqual(config_obj.login_tagline, 'Welcome Alpha!')

    # ── SUPPORT TICKETS TESTS ─────────────────────────────────────────────────
    def test_ticket_flow(self):
        self.client.login(username='superadmin', password='Password123')
        ticket = SupportTicket.objects.create(
            organization=self.org,
            title="Database lock slow",
            description="DB lock is causing delays",
            category="technical",
            priority="high",
            status="open"
        )
        # 1. Detail view
        response = self.client.get(reverse('support_ticket_detail', args=[ticket.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Database lock slow")

        # 2. Update view
        data = {
            'status': 'resolved',
            'priority': 'medium',
            'resolution_notes': 'Fixed the locking issue',
            'assigned_to': self.superadmin_user.pk
        }
        response = self.client.post(reverse('support_ticket_update', args=[ticket.pk]), data=data)
        self.assertRedirects(response, reverse('support_ticket_detail', args=[ticket.pk]))
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'resolved')
        self.assertEqual(ticket.priority, 'medium')
        self.assertEqual(ticket.assigned_to, self.superadmin_user)
        self.assertIsNotNone(ticket.resolved_at)
