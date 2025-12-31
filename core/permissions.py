from rest_framework.permissions import BasePermission
from django.http import HttpResponseForbidden


class IsAdminOrSuperUser(BasePermission):
    """
    Django REST Framework permission class that grants access only to admin users.
    
    Uses role-based authentication instead of hardcoded user IDs for better security
    and maintainability across different environments.
    
    Usage:
        permission_classes = [IsAdminOrSuperUser]
    """ 
    message = 'You do not have permission to perform this action.'
    
    def has_permission(self, request, view):
        """
        Check if user has permission to access the view.
            
        Args:
            request: The incoming request object
            view: The target view being accessed
            
        Returns:
            bool: True if user has admin role, False otherwise
        """
        # Step 1: Ensure user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Step 2: Check admin role - using getattr for safe access
        is_admin = getattr(request.user, 'role', None) == 'admin'
        
        # Step 3: Grant access only to admin users
        return is_admin


def admin_or_superuser_required(view_func):
    """
    Django view decorator that restricts access to admin users.
    
    Uses role-based authentication for consistency across the application.
    
    Usage:
        @admin_or_superuser_required
        def my_admin_view(request):
            # View logic here
    """
    def wrapper(request, *args, **kwargs):
        """
        Wrapper function that performs the permission check.
            
        Args:
            request: The HTTP request object
            *args: Positional arguments for the view
            **kwargs: Keyword arguments for the view
            
        Returns:
            HttpResponse: Original view response or 403 error
        """
        # Step 1: Verify user exists and has admin role
        user_authorized = (
            request.user and 
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'admin'
        )
        
        # Step 2: Execute view if authorized, return error otherwise
        if user_authorized:
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("No tienes permisos para esta acción.")
    
    return wrapper