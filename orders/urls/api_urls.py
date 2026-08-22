

from django.urls import path
from orders.views.api.orders import OrderAPI
from orders.views.api.payments import PaymentAPI
from orders.views.api.shipments import ShipmentAPI

urlpatterns = [
    path("order-form/", OrderAPI.as_view(), name="valid_order_form"),
    
    # --- Shipment Methods Endpoints ---
    path('api/shipments/', ShipmentAPI.as_view(), 
        name='api_shipments'), # GET List
    
    path('api/shipments/<int:pk>/', ShipmentAPI.as_view(), 
        name='api_shipments_detail'), # GET (detail), PATCH
    
    # --- Payment Methods Endpoints ---
    path('api/payments/', PaymentAPI.as_view(), 
        name='api_payments'), # GET List
    
    path('api/payments/<int:pk>/', PaymentAPI.as_view(), 
        name='api_payments_detail'), # GET (detail), PATCH
    
]
