from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from .middleware import AutoLogout

class AutoLogoutMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_anonymous_user_passes_through(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        middleware = AutoLogout(lambda req: "passed")
        response = middleware(request)
        self.assertEqual(response, "passed")

    def test_authenticated_user_passes_through_active_session(self):
        request = self.factory.get('/')
        request.user = self.user
        
        # Setup session support
        middleware_session = SessionMiddleware(lambda req: None)
        middleware_session.process_request(request)
        request.session.save()
        
        # Setup messages support
        middleware_msg = MessageMiddleware(lambda req: None)
        middleware_msg.process_request(request)

        middleware = AutoLogout(lambda req: "passed")
        response = middleware(request)
        self.assertEqual(response, "passed")


from django.urls import reverse
from .models import Hostel, Role, UserProfile

class HostelCRUDTests(TestCase):
    def setUp(self):
        # Create Super Admin Role & User
        self.superadmin_role = Role.objects.create(name='Super Admin', is_superadmin=True)
        self.admin_user = User.objects.create_user(username='admin', password='password')
        self.admin_profile = UserProfile.objects.create(user=self.admin_user, role=self.superadmin_role)

        # Create Standard User without admin permissions
        self.normal_role = Role.objects.create(name='Warden', is_superadmin=False)
        self.normal_user = User.objects.create_user(username='warden', password='password')
        self.normal_profile = UserProfile.objects.create(user=self.normal_user, role=self.normal_role)

        # Create dummy hostel for testing list, edit, delete
        self.hostel = Hostel.objects.create(
            name="Test Hostel",
            code="TH-01",
            hostel_type="Boys",
            capacity=100,
            is_active=True
        )

    def test_list_view_denied_to_anonymous(self):
        response = self.client.get(reverse('hostel_management_list'))
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('hostel_management_list'))

    def test_list_view_forbidden_to_non_admin(self):
        self.client.login(username='warden', password='password')
        response = self.client.get(reverse('hostel_management_list'))
        self.assertEqual(response.status_code, 403)  # PermissionDenied

    def test_list_view_allowed_to_superadmin(self):
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('hostel_management_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.hostel.name)

    def test_create_hostel_post(self):
        self.client.login(username='admin', password='password')
        data = {
            'name': 'New Hostel',
            'code': 'NH-02',
            'hostel_type': 'Girls',
            'email': 'new@hostel.com',
            'phone_number': '1234567890',
            'theme_color': '#0d6efd',
            'capacity': 150,
            'is_active': True,
            'separate_academic_year': True,
            'separate_fee_structure': False,
            'separate_staff_assignment': True,
            'separate_inventory': False,
            'separate_notifications': True,
            'separate_visitor_policy': False,
            'separate_leave_policy': True,
            'separate_attendance_rules': False,
        }
        response = self.client.post(reverse('hostel_management_create'), data=data)
        self.assertRedirects(response, reverse('hostel_management_list'))
        self.assertTrue(Hostel.objects.filter(code='NH-02').exists())
        nh = Hostel.objects.get(code='NH-02')
        self.assertEqual(nh.name, 'New Hostel')
        self.assertEqual(nh.capacity, 150)
        self.assertTrue(nh.separate_academic_year)
        self.assertFalse(nh.separate_fee_structure)

    def test_edit_hostel_post(self):
        self.client.login(username='admin', password='password')
        data = {
            'name': 'Updated Test Hostel',
            'code': 'TH-01-UPDATED',
            'hostel_type': 'Mixed',
            'email': 'updated@hostel.com',
            'phone_number': '0987654321',
            'theme_color': '#0d6efd',
            'capacity': 120,
            'is_active': False,
            'separate_academic_year': False,
            'separate_fee_structure': True,
            'separate_staff_assignment': False,
            'separate_inventory': True,
            'separate_notifications': False,
            'separate_visitor_policy': True,
            'separate_leave_policy': False,
            'separate_attendance_rules': True,
        }
        response = self.client.post(reverse('hostel_management_edit', args=[self.hostel.pk]), data=data)
        self.assertRedirects(response, reverse('hostel_management_list'))
        self.hostel.refresh_from_db()
        self.assertEqual(self.hostel.name, 'Updated Test Hostel')
        self.assertEqual(self.hostel.code, 'TH-01-UPDATED')
        self.assertEqual(self.hostel.capacity, 120)
        self.assertFalse(self.hostel.is_active)
        self.assertTrue(self.hostel.separate_fee_structure)
        self.assertFalse(self.hostel.separate_academic_year)

    def test_delete_hostel_prevents_if_only_one(self):
        self.client.login(username='admin', password='password')
        # At setUp, only 1 hostel exists (self.hostel). Let's try to delete it
        response = self.client.post(reverse('hostel_management_delete', args=[self.hostel.pk]))
        self.assertRedirects(response, reverse('hostel_management_list'))
        self.assertTrue(Hostel.objects.filter(pk=self.hostel.pk).exists())

    def test_delete_hostel_succeeds_if_multiple(self):
        # Create second hostel so total count > 1
        Hostel.objects.create(name="Another Hostel", code="AH-02", hostel_type="Mixed", capacity=50)
        self.client.login(username='admin', password='password')
        self.assertEqual(Hostel.objects.count(), 2)
        
        response = self.client.post(reverse('hostel_management_delete', args=[self.hostel.pk]))
        self.assertRedirects(response, reverse('hostel_management_list'))
        self.assertFalse(Hostel.objects.filter(pk=self.hostel.pk).exists())
        self.assertEqual(Hostel.objects.count(), 1)


