

from django.urls import path
from orders.views_api import * 



urlpatterns = [
    
    path("order-form/", OrderAPI.as_view(), name="valid_order_form"),
    
    
    path("api/shipments/<int:shipment_id>/", ShipmentAPI.as_view(), name="update_shipment"),
    path("api/payments/<int:payment_id>/", PaymentAPI.as_view(), name="update_payment"),
]

