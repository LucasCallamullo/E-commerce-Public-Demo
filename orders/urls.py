

from django.urls import path
from orders import views


urlpatterns = [
    path('resumen-orden/', views.resume_order, name='resume-order'),
    path('detalle-orden/<int:order_id>/', views.order_detail, name='order-detail'),
]