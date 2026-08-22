from datetime import timedelta
from django.db import transaction
from django.utils import timezone

from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.response import Response

from orders.models import (
    ShipmentMethod, ShipmentOrder, PaymentMethod, Order, ItemOrder
)

from cart.models import CartItem
from products.models.product import Product

from core.utils.utils_parsers import valid_id_or_None

def get_order_detail_context(order_id, user):
    # Optimización de consultas con select_related
    order_id = valid_id_or_None(order_id)
    if not order_id:
        return None
    
    order = Order.objects.filter(id=order_id)
    if user.role != 'admin':
        order = order.filter(user=user)
        
    order = (
        order
        .values(
            'id', 'created_at', 'expire_at', 'email', 'name', 'shipment_cost', 'total', 'discount_coupon',
            'shipment__id', 'shipment__address', 
            'status__id', 'status__name',
            'payment__id', 'payment__name', 'payment__time', 
            'shipment__method__id', 'shipment__method__name'
        )
        .first()
    )
    
    if not order:
        return None
    
    # Extraemos y eliminamos datos de forma limpia
    shipment = {
        'id': order.pop('shipment__id'),
        'address': order.pop('shipment__address'),
        'method': {
            'id': order.pop('shipment__method__id'),
            'name': order.pop('shipment__method__name'),
        }
    }

    payment = {
        'id': order.pop('payment__id'),
        'name': order.pop('payment__name'),
        'time': order.pop('payment__time'),
    }

    status = {
        'id': order.pop('status__id'),
        'name': order.pop('status__name'),
    }
        
    items_data = (
        ItemOrder.objects
        .filter(order_id=order_id)
        .values(
            'quantity', 'final_price', 'original_price', 'discount',
            'product__id', 'product__name', 'product__main_image'
        )
    )
    
    processed_items = []
    for item in items_data:
        product = {
            'id': item.pop('product__id'),
            'name': item.pop('product__name'),
            'main_image': item.pop('product__main_image'),
        }
        item['product'] = product
        processed_items.append(item)
    
    context = {
        'items': processed_items,
        'order': order,
        'shipment': shipment,
        'payment': payment,
        'status': status
    }
    return context
