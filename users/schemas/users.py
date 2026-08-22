

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
    OpenApiParameter,
)
from drf_spectacular.types import OpenApiTypes

from core.schemas.errors import AUTH_401_RESPONSE, PERMISSION_403_RESPONSE, invalid_id_response, not_found_response
from users.serializers.users import UserSerializer, UserMeSerializer
from users.serializers.docs import (
    UserListResponseSerializer, UserRoleUpdateRequestSerializer, UserRoleUpdateResponseSerializer
)


class UserSchemas:
    # --- GET /api/v1/users ---
    get_list = extend_schema(
        summary="List users",
        description="Retrieve a paginated list of users with optional search filters. "
                   "Only accessible by administrators.",
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Text to search for in user fields',
                examples=[
                    OpenApiExample(
                        'Search by name',
                        value='john',
                        description='Search for users with "john" in their name'
                    ),
                    OpenApiExample(
                        'Search by DNI',
                        value='12345678',
                        description='Search for user with specific DNI'
                    ),
                ]
            ),
            OpenApiParameter(
                name='filter',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Field to filter by',
                enum=['dni', 'name', 'email', 'cellphone'],
                examples=[
                    OpenApiExample('Filter by name', value='name'),
                    OpenApiExample('Filter by email', value='email'),
                    OpenApiExample('Filter by DNI', value='dni'),
                    OpenApiExample('Filter by cellphone', value='cellphone'),
                ]
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=UserListResponseSerializer(many=True),
                description='List of users retrieved successfully',
                examples=[
                    OpenApiExample(
                        'Success response',
                        value={
                            "success": True,
                            "count": 25,
                            "users": [
                                {
                                    "id": 1,
                                    "dni": "12345678",
                                    "first_name": "John",
                                    "last_name": "Doe",
                                    "email": "john.doe@example.com",
                                    "cellphone": "+541112345678",
                                    "profile_image": "http://example.com/media/profile_images/john.jpg"
                                }
                            ]
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Invalid filter parameter',
                examples=[
                    OpenApiExample(
                        'Invalid filter error',
                        value={
                            "success": False,
                            "detail": "Invalid filter parameter."
                        }
                    )
                ]
            ),
            401: AUTH_401_RESPONSE,
            403: PERMISSION_403_RESPONSE,
        },
        tags=['Users'],
        operation_id='list_users',
    ),
    
    # --- POST /api/v1/users ---
    create = extend_schema(
        summary="Create user",
        description="Create a new user account for sales simulations. "
                   "Profile images are handled separately via the dedicated image upload endpoint.",
        request=UserSerializer,  # ¡Directo, no en dict!
        tags=['Users'],
        operation_id='create_user',
        examples=[
            OpenApiExample(
                'Create User Request',
                description='JSON payload for creating a new user',
                value={
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "dni": "12345678",
                    "cellphone": "+541112345678"
                    # NOTA: No incluye 'password' ni 'profile_image'
                    # NOTA: 'id' y 'role' son read_only en el serializer
                },
                request_only=True,
                media_type='application/json'  # ← ¡IMPORTANTE! JSON, no multipart
            ),
        ],
        responses={
            201: OpenApiResponse(
                response=UserSerializer,
                description='User created successfully',
                examples=[
                    OpenApiExample(
                        'Success Response',
                        value={
                            "success": True,
                            "user": {
                                "id": 26,
                                "dni": "87654321",
                                "first_name": "Jane",
                                "last_name": "Smith",
                                "email": "jane.smith@example.com",
                                "cellphone": "+5491133445566",
                                "role": "client"  # ← Se agrega automáticamente
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,    # importante para formatear el error
                description='Validation error',
                examples=[
                    OpenApiExample(
                        'Email already exists',
                        value={
                            "email": ["Ese email ya está registrado."]
                        }
                    )
                ]
            ),
            401: AUTH_401_RESPONSE,
            403: PERMISSION_403_RESPONSE,
        }
    )
    
    # --- PATCH /api/v1/users/{id}/role/ ---
    update_role = extend_schema(
        summary="Update user role",
        description="Update the role of a user. Only administrators can perform this action.",
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='ID of the user whose role will be updated'
            )
        ],
        request=UserRoleUpdateRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=UserRoleUpdateResponseSerializer,
                description="User role updated successfully",
                examples=[
                    OpenApiExample(
                        'Success response',
                        value={
                            "success": True,
                            "detail": "Rol actualizado correctamente",
                            "user": {
                                "id": 10,
                                "role": "admin"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Invalid input data",
                examples=[
                    invalid_id_response("User"),
                    OpenApiExample(
                        name="Invalid role",
                        summary="Role validation error",
                        value={
                            "role": ["El rol debe ser uno de: 'admin', 'seller' o 'buyer'"]
                        }
                    ),
                ]
            ),
            401: AUTH_401_RESPONSE,
            403: PERMISSION_403_RESPONSE,
            404: not_found_response("User"),
        },
        tags=['Users'],
        operation_id='update_user_role',
    )
    
    
    # --- PATCH /api/v1/users/me/ ---
    me_update = extend_schema(
        summary="Update own user profile",
        description=(
            "Partially update the authenticated user's profile. "
            "Only personal, non-sensitive fields can be modified. "
            "Fields not provided or sent as empty strings are ignored."
        ),
        request=UserMeSerializer,
        responses={
            200: OpenApiResponse(
                description="Profile updated successfully",
                response=UserMeSerializer,
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "success": True,
                            "detail": "Profile updated successfully.",
                            "user": {
                                "first_name": "Juan",
                                "last_name": "Perez",
                                "cellphone": "123456789",
                                "province": "BA",
                                "address": "Av. Siempre Viva 742",
                                "dni": "12345678"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Validation error",
                examples=[
                    OpenApiExample(
                        name="Invalid field",
                        value={
                            "dni": ["This field must contain only numbers."]
                        }
                    )
                ]
            ),
            401: AUTH_401_RESPONSE,
        },
        tags=["Users"],
    )
