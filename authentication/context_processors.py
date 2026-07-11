"""
RBAC Context Processor.

Injects permission data and sidebar-visible modules into every template context.
Result is cached on the request object to avoid multiple DB hits per request.
"""

from .models import Module, RolePermission


def rbac_context(request):
    """
    Adds to template context:
      user_permissions  — dict  {module_code: {action: bool, ...}}
      visible_modules   — list  of Module objects the user has can_view=True on
      is_superadmin     — bool
    """
    if not request.user.is_authenticated:
        return {
            'user_permissions': {},
            'visible_modules': [],
            'is_superadmin': False,
        }

    # Use per-request cache to avoid duplicate DB queries
    if hasattr(request, '_rbac_cache'):
        return request._rbac_cache

    profile = None
    try:
        profile = request.user.profile
    except Exception:
        pass

    is_super = (
        request.user.is_superuser or (
            profile and
            profile.role and
            profile.role.is_superadmin
        )
    )

    all_modules = list(Module.objects.order_by('order', 'name'))

    if is_super:
        # Super admin sees everything with all actions enabled
        ALL_ACTIONS = ['view', 'add', 'edit', 'delete', 'approve', 'reject',
                       'export', 'print', 'import', 'hide', 'disable']
        user_permissions = {
            m.code: {action: True for action in ALL_ACTIONS}
            for m in all_modules
        }
        visible_modules = all_modules
    else:
        user_permissions = {}
        visible_modules = []

        if profile and profile.role:
            role = request.user.profile.role
            perms = RolePermission.objects.filter(role=role).select_related('module')

            perm_map = {p.module.code: p for p in perms}

            for module in all_modules:
                perm = perm_map.get(module.code)
                if perm:
                    module_perms = {
                        'view':    perm.can_view,
                        'add':     perm.can_add,
                        'edit':    perm.can_edit,
                        'delete':  perm.can_delete,
                        'approve': perm.can_approve,
                        'reject':  perm.can_reject,
                        'export':  perm.can_export,
                        'print':   perm.can_print,
                        'import':  perm.can_import,
                        'hide':    perm.can_hide,
                        'disable': perm.can_disable,
                    }
                    user_permissions[module.code] = module_perms
                    if perm.can_view and module.url_name:
                        visible_modules.append(module)
                else:
                    user_permissions[module.code] = {
                        action: False
                        for action in ['view', 'add', 'edit', 'delete', 'approve',
                                       'reject', 'export', 'print', 'import', 'hide', 'disable']
                    }

    result = {
        'user_permissions': user_permissions,
        'visible_modules': visible_modules,
        'is_superadmin': is_super,
    }
    request._rbac_cache = result
    return result
