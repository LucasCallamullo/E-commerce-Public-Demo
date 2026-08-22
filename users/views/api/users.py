from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema_view

# my modules
from users.models import CustomUser
from users.services.users import UserService
from users.schemas.users import UserSchemas
from users.serializers.users import UserSerializer, UserMeSerializer

from core.permissions import IsAdminOrSuperUser
from core.utils.utils_parsers import valid_id_or_None


@extend_schema_view(
    patch=UserSchemas.me_update,
)
class UserMeUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        """
        Partially update the authenticated user's profile.
        """
        serializer = UserMeSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
                "success": True,
                "detail": "Profile updated successfully.",
                "user": serializer.data
            }, status=status.HTTP_200_OK
        )


@extend_schema_view(
    patch=UserSchemas.update_role,
)
class UserRoleUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def patch(self, request, user_id):
        """
        Partially update a user's role.
        This endpoint allows an administrator to update the role of a user.

        Args:
            request (Request): DRF request object.
            user_id (str | int): User identifier from the URL.

        Returns:
            Response: JSON response indicating success or failure.
        """
        # Validate user ID
        user_id = valid_id_or_None(user_id)
        if not user_id:
            return Response(
                {"success": False, "detail": "Invalid user ID."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract role from request body
        role = request.data.get("role")
        if not role:
            return Response(
                {"success": False, "detail": "Role is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delegate update logic to the service layer
        try:
            user = UserService.update_user_role(user_id=user_id, role=role)

        except CustomUser.DoesNotExist:
            return Response(
                {"success": False, "detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        except ValueError:
            return Response({
                    "success": False,
                    "detail": "Role must be one of: admin, seller, or buyer."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
                "success": True,
                "detail": "User role updated successfully.",
                "user": user,
            },
            status=status.HTTP_200_OK
        )

    
@extend_schema_view(
    get=UserSchemas.get_list,
    post=UserSchemas.create,
)
class UserAPIView(APIView):
    """
    User management API for administrators.
    
    Provides endpoints for:
    - Listing and searching users with various filters
    - Creating new users (primarily for sales simulation scenarios)
    
    Permissions: Requires admin or superuser role.
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    
    def get(self, request):
        """Retrieve filtered list of users."""
        search = request.query_params.get("search", "").strip()
        filter_by = request.query_params.get("filter", "") # dni, name, email, cellphone

        # Reject invalid filter parameters early
        flag = filter_by in ("dni", "name", "email", "cellphone")
        if search and not flag:
            return Response({
                    "success": False,
                    "detail": "Invalid filter parameter."
                }, status=status.HTTP_400_BAD_REQUEST
            )

        # Apply filters only if both search text and filter type are provided - return a list
        if search and flag:
            users = UserService.get_users_for_sale(search=search, filter_by=filter_by)
        else:
            users = UserService.get_all_limit_for_sale(30)

        return Response({
            "success": True,
            "count": len(users),
            "users": users
        }, status=status.HTTP_200_OK)
    
    
    def post(self, request):
        """Create a new user account."""
        
        serializer = UserSerializer(data=request.data)
        
        # estandar drf --> devuelve los errores del serializer con error 400
        serializer.is_valid(raise_exception=True)
        
        # Es equivalente a esto, lo dejo comentado pero es la forma explicita a la anterior linea implicita
        # if not serializer.is_valid():
            # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        client = serializer.save()
        return Response({
            "success": True,
            "user": UserSerializer(client).data
        }, status=status.HTTP_201_CREATED)
        

""" 
NOTE capaz en un futuro para mejorar la performance del get usar vectores propios de POSTGRESQL,
sería lo ideal pero de momento no es necesario.

from django.contrib.postgres.search import (
    SearchVector,
    SearchQuery,
    SearchRank,
)

# PostgreSQL Full-Text Search (recommended for large datasets)
#
# This approach:
# - Tokenizes the text
# - Ignores accents (depending on configuration)
# - Is much faster at scale
# - Allows result ranking
#
# search_query = SearchQuery(search)
#
# queryset = queryset.annotate(
#     search_vector=SearchVector('first_name', 'last_name'),
#     rank=SearchRank(
#         SearchVector('first_name', 'last_name'),
#         search_query
#     )
# ).filter(
#     search_vector=search_query
# ).order_by('-rank')
"""
