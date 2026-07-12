"""
White-label middleware for organizations.
Detects the request subdomain/domain and resolves the matching Organization,
injecting it and its branding config into the request object.
"""
from django.shortcuts import redirect
from django.urls import reverse
from .models import Organization


class WhiteLabelMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.organization = None
        request.org_branding = None

        host = request.get_host().split(':')[0].lower()

        try:
            # 1. Try exact custom_domain match (e.g. hms.university.edu)
            org = Organization.objects.filter(
                custom_domain__iexact=host
            ).select_related('whitelabel').first()

            # 2. Try subdomain match (e.g. abc.yourerp.com → subdomain='abc')
            if not org:
                parts = host.split('.')
                if len(parts) >= 3:
                     subdomain = parts[0]
                     org = Organization.objects.filter(
                         subdomain__iexact=subdomain
                     ).select_related('whitelabel').first()

            if org:
                request.organization = org
                try:
                    request.org_branding = org.whitelabel
                except Exception:
                    request.org_branding = None
        except Exception:
            pass

        response = self.get_response(request)
        return response


class SubscriptionCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Skip checking global superusers or portal superadmins
            is_super = request.user.is_superuser
            profile = getattr(request.user, 'profile', None)
            if profile and profile.role and profile.role.is_superadmin:
                is_super = True

            if not is_super and profile and profile.organization:
                org = profile.organization
                
                # Check status
                pending_sub = org.subscriptions.filter(is_active=False, payment_status='pending').first()
                has_active_sub = org.subscriptions.filter(is_active=True, payment_status='active').exists()
                
                # If organization has a pending subscription and no active subscription, redirect to pay page
                if pending_sub and not has_active_sub:
                    pay_url = reverse('org_subscription_pay')
                    logout_url = reverse('logout')
                    
                    if (request.path != pay_url and 
                        request.path != logout_url and 
                        not request.path.startswith('/static/') and 
                        not request.path.startswith('/media/')):
                        return redirect('org_subscription_pay')

        return self.get_response(request)

