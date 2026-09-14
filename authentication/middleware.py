import time
from django.contrib import auth
from django.shortcuts import redirect
from django.conf import settings

class AutoLogout:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('_last_activity')
            now_ts = int(time.time())
            timeout = getattr(settings, 'SESSION_COOKIE_AGE', 900)

            if last_activity is not None and (now_ts - last_activity > timeout):
                auth.logout(request)
                return redirect('login')

            request.session['_last_activity'] = now_ts

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
                '/authentication/keep-alive/',
                '/static/',
                '/media/',
            ]
            if not any(path.startswith(p) for p in exempt_paths):
                profile = getattr(request.user, 'profile', None)
                if not profile or not profile.role:
                    return redirect('no_role')

        return self.get_response(request)