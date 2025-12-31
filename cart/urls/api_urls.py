
from django.urls import path
from cart.views.api.cart import CartAPIView

urlpatterns = [
    
    path('api/cart/', CartAPIView.as_view(), name='cart-api-detail'),  # GET carrito completo
    
    # POST/DELETE producto
    path('api/cart/<int:product_id>/', CartAPIView.as_view(), name='cart-api'),  
]
