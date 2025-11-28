

from rest_framework.permissions import BasePermission

class IsAdminOrSuperUser(BasePermission):
    """
    Permite el acceso solo a usuarios admin o superusuario (id=1)
    """
    message = 'No tienes permisos para esta acción.'  # Mensaje personalizado
    
    def has_permission(self, request, view):
        return bool(request.user and (request.user.id == 1 or request.user.role == 'admin'))
    
    
# user como decorador en django
from django.http import HttpResponseForbidden

def admin_or_superuser_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user and (request.user.id == 1 or request.user.role == 'admin'):
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("No tienes permisos para esta acción.")
    return wrapper