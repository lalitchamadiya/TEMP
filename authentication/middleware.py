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