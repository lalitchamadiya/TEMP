from django import template
from authentication.decorators import check_perm

register = template.Library()


@register.filter(name='has_role')
def has_role(user, role_names):
    if not user.is_authenticated:
        return False

    profile = None
    try:
        profile = user.profile
    except Exception:
        pass

    if user.is_superuser or (profile and profile.role and profile.role.is_superadmin):
        return True
    if profile and profile.role:
        names = [name.strip() for name in role_names.split(',')]
        return profile.role.name in names
    return False


@register.simple_tag
def has_perm(user, module_code, action):
    """
    Usage: {% has_perm user 'student' 'add' %}
    Returns True/False.
    Supports: view, add, edit, delete, approve, reject, export, print, import, hide, disable
    """
    return check_perm(user, module_code, action)


@register.simple_tag(takes_context=True)
def perm(context, module_code, action):
    """
    Shortcut that reads the user from template context automatically.
    Usage: {% perm 'student' 'add' %}
    """
    user = context.get('user') or context.get('request', None) and context['request'].user
    if user is None:
        return False
    return check_perm(user, module_code, action)


@register.filter
def module_perm(user_permissions, lookup):
    """
    Filter for dict lookups: {{ user_permissions|module_perm:'student.add' }}
    Splits on '.' to get module_code and action.
    """
    if not user_permissions or '.' not in lookup:
        return False
    parts = lookup.split('.', 1)
    module_code, action = parts[0], parts[1]
    return user_permissions.get(module_code, {}).get(action, False)


@register.filter
def get_item(dictionary, key):
    if dictionary and hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None


@register.simple_tag
def has_element_perm(user, element_code):
    """
    Usage: {% has_element_perm user 'btn_create_room' %}
    Returns True/False.
    """
    from authentication.decorators import check_element_perm
    return check_element_perm(user, element_code)


@register.filter(name='has_element_perm')
def has_element_perm_filter(user, element_code):
    """
    Usage: {{ user|has_element_perm:'btn_create_room' }}
    Returns True/False.
    """
    from authentication.decorators import check_element_perm
    return check_element_perm(user, element_code)

