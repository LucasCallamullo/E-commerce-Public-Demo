

from django.urls import path
from profiles import views


urlpatterns = [
    
    path('perfil/', views.profile_page, name='profile_user'),
    path('profile/tab/<str:tab_name>/', views.profile_tabs, name='profile_tabs'),
]
