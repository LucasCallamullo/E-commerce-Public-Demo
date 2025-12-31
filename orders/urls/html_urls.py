

from django.urls import path
from orders.views.html.orders import resume_order, order_detail

urlpatterns = [
    path('resumen-orden/', resume_order, name='resume-order'),
    path('detalle-orden/<int:order_id>/', order_detail, name='order-detail'),
]