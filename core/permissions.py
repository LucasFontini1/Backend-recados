from rest_framework.permissions import SAFE_METHODS, BasePermission

def is_portal_admin(user):
    return bool(user and user.is_authenticated and (
        user.is_superuser or user.groups.filter(name__in=['admin', 'superadmin']).exists()
    ))

class AdminGroupModelPermissionsOrReadOnly(BasePermission):
    """Leitura pública; escrita somente para admin com permissão Django."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not is_portal_admin(user):
            return False
        model = view.get_queryset().model
        action = {
            'POST': 'add', 'PUT': 'change', 'PATCH': 'change', 'DELETE': 'delete',
        }.get(request.method)
        return bool(action and user.has_perm(f'{model._meta.app_label}.{action}_{model._meta.model_name}'))

class PortalAdminPermission(BasePermission):
    def has_permission(self, request, view):
        return is_portal_admin(request.user)
