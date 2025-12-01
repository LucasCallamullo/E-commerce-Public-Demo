

from django.db import transaction


from orders.models import ShipmentMethod, ShipmentOrder, PaymentMethod
from orders.models import Order, ItemOrder
from cart.models import CartItem

from datetime import timedelta
from django.utils import timezone


from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.response import Response

from products.utils import valid_id_or_None

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


def create_order_pending(order_data, user, products, quantities):
    from decimal import Decimal
    """
    # example on order data
    order_data = {
        "first_name": "Lucas",
        "last_name": "Martinez",
        "email": "lucas.martinez@example.com",
        "cellphone": "3515437688",
        "dni": "41224335",
        "detail_order": "Por favor, entregar antes de las 18:00.",
        
        # NOTE if id_envio_method == '1': # this is only for retire local
        "name_retire": "lucas",
        "dni_retire": "martinez",
        
        # NOTE if id_envio_method != '1': # Home delivery
        "province": "Córdoba",
        "city": "Córdoba Capital",
        "address": "Av. Colón 1234",
        "postal_code": "5000",
        "detail": "Departamento 2B",
        
        # NOTE this is for use to complete de order
        "shipping_method_id": "2", 
        "payment_method_id": "3"
    }
    """
    # .values() no se aplica sobre get, para simular resultado, usamos filter + first para trear un unico diccionario
    shipping_method = ShipmentMethod.objects.filter(id=order_data['shipping_method_id']).values('id', 'price').first()
    if not shipping_method:
        return None, Response({'detail': 'Método de envío no válido'}, status=HTTP_400_BAD_REQUEST)
    
    # .values() no se aplica sobre get, para simular resultado, usamos filter + first para trear un unico diccionario
    payment_method = PaymentMethod.objects.filter(id=order_data['payment_method_id']).values('id', 'time').first()
    if not payment_method:
        return None, Response({'detail': 'Método de pago no válido'}, status=HTTP_400_BAD_REQUEST)

    # try:    realmente me puedo tomar la libertad de poner status_id = 2, evita consulta
    #    status_order = StatusOrder.objects.only('id').get(id=2)  # Orden en estado "Pendiente"
    # except ShipmentMethod.DoesNotExist:
    #    return None, Response({'detail': 'Estado de orden no válido'}, status=HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        
        # Create shipping order to associate with the order
        shipment = ShipmentOrder.objects.create(
            method_id=shipping_method['id'],
            name_pickup=order_data.get("name_retire", ""),
            dni_pickup=order_data.get("dni_retire", ""),
            address=order_data.get("address", ""),
            province=order_data.get("province", ""),
            city=order_data.get("city", ""),
            postal_code=order_data.get("postal_code", ""),
            detail=order_data.get("detail", ""),
        )
        
        # Create expired time for the order, to apply maybe with a signal?
        expire_at = timezone.now() + timedelta(hours=payment_method['time'])
        name = f'{order_data.get("first_name", "")} {order_data.get("last_name", "")}'
        # Create new Order
        new_order = Order.objects.create(
            user=user,
            status_id=2,    # status_order
            payment_id=payment_method['id'],
            shipment=shipment,
            name=name,
            email=order_data.get("email", ""),
            cellphone=order_data.get("cellphone", ""),
            dni=order_data.get("dni", ""),
            detail_order=order_data.get("detail_order", ""),
            expire_at=expire_at
        )
        
        # crear order items
        order_items = []
        
        # update post
        subtotal = 0
        shipment_cost = shipping_method['price']
        # maybe more logic like coupon model in the future
        # discount = Decimal(order_data.get("discount", "0"))    
        discount_coupon = Decimal("2.00")
        
        for product_id, product in products.items():
            quantity = quantities.get(product_id)['quantity']
            
            if product is None:
                transaction.set_rollback(True)
                return None, Response({'detail': 'Productos no validos.'}, status=HTTP_400_BAD_REQUEST)
            
            # Calcular subtotal de productos
            price_decimal = product.calc_discount_decimal()
            subtotal += ( price_decimal * quantity )    # get decimal * int = decimal
            
            order_items.append(ItemOrder(
                order=new_order,
                product=product,
                discount=product.discount,
                original_price=product.price,
                quantity=quantity,
                final_price=price_decimal
            ))
                
        ItemOrder.objects.bulk_create(order_items)
        
        # Eliminar items del carrito solo si todo lo anterior salió bien
        CartItem.objects.filter(id__in=[v['item_id'] for v in quantities.values()]).delete()
        
        # Calcular total
        total = subtotal + shipment_cost - discount_coupon

        # Actualizar la orden con estos campos
        new_order.shipment_cost = shipment_cost
        new_order.discount_coupon = discount_coupon
        new_order.total = total
        new_order.save(update_fields=["shipment_cost", "discount_coupon", "total"])
        
    return new_order, None
    
    
from products.models import Product
def confirm_stock_availability(cart):
    """
    Optimized function to reserve stock for products in the user's cart.
    Uses atomic transactions and row-level locking to prevent race conditions.

    Args:
        cart (Cart): The cart instance for the current user.

    Returns:
        dict: {'products': {product_id: Product}, 'quantities': {product_id: quantity}} 
              if stock reservation succeeds.
        None, Response: DRF Response with error detail if stock is insufficient or cart is empty.
    """
    # Retrieve cart items as dictionaries to avoid loading full model instances
    cart_items = (
        CartItem.objects
        .filter(cart=cart)
        .values('id', 'quantity', 'product__id')
    )

    with transaction.atomic():
        # Check if cart is empty
        if not cart_items.exists():
            transaction.set_rollback(True)
            return None, Response({'detail': 'No hay productos agregados'}, status=HTTP_400_BAD_REQUEST)

        # Prepare product IDs and quantities dictionary
        product_ids = []
        quantities = {}
        for item in cart_items:
            quantities[item['product__id']] = {'quantity': item['quantity'], 'item_id': item['id']} 
            product_ids.append(item['product__id'])

        # Fetch products in bulk with row-level locking to prevent concurrent stock modifications
        products = (
            Product.objects
            .filter(id__in=product_ids)
            .select_for_update()
            .only('id', 'name', 'stock', 'stock_reserved', 'available', 'price', 'discount')
            .in_bulk()  # Returns a dict {id: Product instance}
        )

        # Prepare list for bulk update
        modified_products = []

        for product_id, product in products.items():
            quantity = quantities.get(product_id)['quantity']  # default None if not found

            # Reserve stock in memory
            if quantity is None or not product.make_stock_reserved(quantity):
                transaction.set_rollback(True)
                return None, Response({'detail': f'Stock Insuficiente {product.name}'}, status=HTTP_400_BAD_REQUEST)

            modified_products.append(product)

        # Commit all stock changes in a single bulk update
        Product.objects.bulk_update(modified_products, ['stock', 'stock_reserved'])

    # Return products and quantities to continue with order creation
    return {'products': products, 'quantities': quantities}, None

