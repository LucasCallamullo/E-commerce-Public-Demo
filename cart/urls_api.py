

from django.urls import path
from cart.views_api import CartAPIView

urlpatterns = [
    path('api/cart/<int:product_id>/', CartAPIView.as_view(), name='cart-api'),
]