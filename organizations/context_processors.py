"""
Context processor for white-label organization branding.
Exposes org_branding and current_org to all templates.
"""


def org_branding_context(request):
    context = {
        'current_org': None,
        'org_branding': None,
    }

    try:
        if hasattr(request, 'organization') and request.organization:
            context['current_org'] = request.organization
            context['org_branding'] = getattr(request, 'org_branding', None)
    except Exception:
        pass

    return context
