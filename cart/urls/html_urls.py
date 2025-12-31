
from django.urls import path
from cart.views.html.cart import cart_page_detail

urlpatterns = [
    path('ver-carrito/', cart_page_detail, name='cart_page_detail'),
]
