

from django.urls import path
from cart import views

urlpatterns = [
    path('ver-carrito/', views.cart_page_detail, name='cart_page_detail'),
]