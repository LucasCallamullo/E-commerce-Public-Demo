

from django.urls import path
from contact import views

urlpatterns = [
    path('contacto/', views.contact_info, name='contact'),
] 