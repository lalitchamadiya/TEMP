from django.utils import timezone
from .models import AuditLog


class AuditableMixin:
    """
    Mixin for class-based views to automatically log administrative/CRUD actions.
    Can be used with CreateView, UpdateView, DeleteView, or generic Views.
    """
    audit_action = None  # e.g., 'create', 'edit', 'delete'
    audit_log_details = ''  # Custom details message or format string

    def get_audit_action(self):
        if self.audit_action:
            return self.audit_action
        
        view_name = self.__class__.__name__.lower()
        if 'create' in view_name or 'add' in view_name:
            return 'create'
        elif 'update' in view_name or 'edit' in view_name:
            return 'edit'
        elif 'delete' in view_name:
            return 'delete'
        return 'edit'

    def get_audit_details(self, obj=None):
        if self.audit_log_details:
            return self.audit_log_details
        
        obj_name = str(obj) if obj else "Object"
        action = self.get_audit_action()
        return f"{self.__class__.__name__}: Auto-logged {action} on {obj_name}"

    def get_audit_target_user(self, obj=None):
        from django.contrib.auth.models import User
        if isinstance(obj, User):
            return obj
        if obj and hasattr(obj, 'user') and isinstance(obj.user, User):
            return obj.user
        return None

    def log_audit(self, obj=None):
        user = self.request.user if hasattr(self, 'request') and self.request.user.is_authenticated else None
        if not user:
            return

        # Determine Client IP Address
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR')

        action = self.get_audit_action()
        target_user = self.get_audit_target_user(obj)
        details = self.get_audit_details(obj)

        AuditLog.objects.create(
            actor=user,
            target_user=target_user,
            action=action,
            details=details,
            ip_address=ip,
            timestamp=timezone.now()
        )

    def dispatch(self, request, *args, **kwargs):
        """Standard hook for generic Django View classes."""
        response = super().dispatch(request, *args, **kwargs)
        # Log deletion audit on successful delete
        if request.method == 'POST' and self.get_audit_action() == 'delete' and response.status_code in [302, 200]:
            self.log_audit(getattr(self, 'object', None))
        return response

    def form_valid(self, form):
        """Standard hook for CreateView and UpdateView."""
        response = super().form_valid(form)
        # self.object is populated by CreateView/UpdateView form_valid
        self.log_audit(self.object)
        return response
