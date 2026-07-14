from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from .middleware import AutoLogout
from .models import Role, PermissionElement, RoleElementPermission, UserProfile
from .decorators import check_element_perm
from .templatetags.rbac_tags import has_element_perm


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


class RoleElementPermissionTest(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name='WardenTest', description='Temporary test role')
        self.user = User.objects.create_user(username='wardentest', password='password')
        self.profile = UserProfile.objects.create(user=self.user, role=self.role)
        
        self.element = PermissionElement.objects.create(
            code='btn_test_action',
            name='Test Action Button',
            category='button'
        )

    def test_permission_denied_by_default(self):
        # By default, without RoleElementPermission record, access is denied
        self.assertFalse(check_element_perm(self.user, 'btn_test_action'))
        self.assertFalse(has_element_perm(self.user, 'btn_test_action'))

    def test_permission_allowed_when_enabled(self):
        # Create permission record and set is_enabled = True
        RoleElementPermission.objects.create(
            role=self.role,
            element=self.element,
            is_enabled=True
        )
        self.assertTrue(check_element_perm(self.user, 'btn_test_action'))
        self.assertTrue(has_element_perm(self.user, 'btn_test_action'))

    def test_permission_denied_when_disabled(self):
        # Create permission record and set is_enabled = False
        RoleElementPermission.objects.create(
            role=self.role,
            element=self.element,
            is_enabled=False
        )
        self.assertFalse(check_element_perm(self.user, 'btn_test_action'))
        self.assertFalse(has_element_perm(self.user, 'btn_test_action'))

    def test_superadmin_always_allowed(self):
        # Role name super admin or is_superuser should pass regardless
        sa_role = Role.objects.create(name='Super Admin', description='Super admin role', is_superadmin=True)
        sa_user = User.objects.create_user(username='sa', password='password')
        UserProfile.objects.create(user=sa_user, role=sa_role)
        
        self.assertTrue(check_element_perm(sa_user, 'btn_test_action'))
        self.assertTrue(has_element_perm(sa_user, 'btn_test_action'))

from django.urls import reverse
from .models import SystemSettings


class SystemSettingsVerificationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='superadmin', password='password')
        self.role = Role.objects.create(name='Super Admin', description='SA role', is_superadmin=True)
        UserProfile.objects.create(user=self.user, role=self.role)

    def test_system_settings_save_and_retrieve(self):
        self.client.force_login(self.user)
        url = reverse('system_settings_view')
        response = self.client.post(url, {
            'system_name': 'Test Hostel',
            'organization_name': 'Test Org',
            'theme_color': '#6366f1',
            'timezone': 'UTC',
            'date_format': 'Y-m-d',
            'time_format': 'H:i:s',
            'currency': 'USD',
            'language': 'en',
            'system_version': '1.0.0',
            'session_timeout': 3600,
            'login_attempt_limit': 10,
            'allowed_ips': '192.168.1.1, 10.0.0.0/24',
            'enable_audit_logs': True,
            'password_expiry_days': 30,
            'backup_frequency': 'weekly',
        })
        self.assertEqual(response.status_code, 302)
        
        settings = SystemSettings.get_settings()
        self.assertEqual(settings.system_name, 'Test Hostel')
        self.assertEqual(settings.session_timeout, 3600)
        self.assertEqual(settings.login_attempt_limit, 10)
        self.assertEqual(settings.allowed_ips, '192.168.1.1, 10.0.0.0/24')
        self.assertTrue(settings.enable_audit_logs)
        self.assertEqual(settings.password_expiry_days, 30)
        self.assertEqual(settings.backup_frequency, 'weekly')
