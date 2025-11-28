

from django.urls import path
from users.views_api import *

urlpatterns = [
    path('widget-login/', LoginView.as_view(), name='widget_login'),
    path('close-session/', CloseView.as_view(), name='close_session'),
    path('register-session/', RegisterUserView.as_view(), name='register_user'),
    
    # panel de admin users changes roles
    path('api/user/role/<int:user_id>/', UserRoleEditView.as_view(), name='user_edit_role'),
]

