from django.urls import path

from users.views.api.session import (
    LoginView,
    CloseView,
    RegisterUserView,
)

from users.views.api.users import (
    UserAPIView,
    UserRoleUpdateAPIView,
    UserMeUpdateAPIView,
)

from users.views.api.reset_pw import PasswordResetConfirmView, PasswordResetRequestView


urlpatterns = [
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/logout/', CloseView.as_view(), name='logout'),
    path('api/auth/register/', RegisterUserView.as_view(), name='register'),

    # Admin: list and create users
    path('api/v1/users/', UserAPIView.as_view(), name='users_list_create'),

    # Admin: update user role
    path(
        'api/v1/users/<int:user_id>/role/',
        UserRoleUpdateAPIView.as_view(),
        name='user_update_role'
    ),

    # Authenticated user: update own profile
    path('api/v1/users/me/', UserMeUpdateAPIView.as_view(), name='user_me'),
    
    # ------------ views to reset pw
    path('api/auth/password-reset/', 
        PasswordResetRequestView.as_view(), 
        name='api_password_reset'),
    
    path('api/auth/password-reset/confirm/', 
        PasswordResetConfirmView.as_view(), 
        name='api_password_reset_confirm'),
]
