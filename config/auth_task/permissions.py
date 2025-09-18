from rest_framework import permissions
from .models import AccessRule

class CustomPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        action_map = {
            'GET': 'read',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        
        action = action_map.get(request.method)
        element_name = view.business_element
        
        try:
            rule = AccessRule.objects.get(role=request.user.role, element__name=element_name)
            permission_attr = f"{action}_permission"
            if hasattr(rule, permission_attr):
                return getattr(rule, permission_attr)
        except AccessRule.DoesNotExist:
            return False
        
        return False