from django.urls import path
from users.views.html.users import ResetPasswordPageView, register_user

urlpatterns = [
    path('register-user/', register_user, name='register_user_page'),
    
    # Esta página muestra el formulario para reset pw
    path('reset-password/<str:uidb64>/<str:token>/', 
        ResetPasswordPageView.as_view(), 
        name='reset_password_page'),
]

