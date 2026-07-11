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

