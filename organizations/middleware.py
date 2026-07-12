"""
White-label middleware for organizations.
Detects the request subdomain/domain and resolves the matching Organization,
injecting it and its branding config into the request object.
"""
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
                custom_domain__iexact=host, is_active=True
            ).select_related('whitelabel').first()

            # 2. Try subdomain match (e.g. abc.yourerp.com → subdomain='abc')
            if not org:
                parts = host.split('.')
                if len(parts) >= 3:
                    subdomain = parts[0]
                    org = Organization.objects.filter(
                        subdomain__iexact=subdomain, is_active=True
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
