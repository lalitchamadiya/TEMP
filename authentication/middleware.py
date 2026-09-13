from django.contrib import auth, messages
from django.contrib.sessions.models import Session
from django.shortcuts import redirect
from django.utils import timezone

class AutoLogout:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_session_key = request.session.session_key
            sessions = Session.objects.filter(expire_date__lte=timezone.now())
            for session in sessions:
                if session.session_key == current_session_key:
                    auth.logout(request)
                    messages.success(request, "You have been logged out due to inactivity")
                    return redirect('login')

        return self.get_response(request)


class NoRoleAccessMiddleware:
    """
    Middleware that intercepts requests from logged-in non-superusers.
    If the user has no assigned role (profile.role is None), restricts them
    from accessing system endpoints and redirects to the 'no_role' page.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            path = request.path
            exempt_paths = [
                '/authentication/no-role/',
                '/authentication/logout/',
                '/authentication/login/',
                '/static/',
                '/media/',
            ]
            if not any(path.startswith(p) for p in exempt_paths):
                profile = getattr(request.user, 'profile', None)
                if not profile or not profile.role:
                    return redirect('no_role')

        return self.get_response(request)