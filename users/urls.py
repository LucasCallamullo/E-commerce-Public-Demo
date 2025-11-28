

from django.urls import path
from users import views


urlpatterns = [
    path('register-user/', views.register_user, name='register_user_page'),
]