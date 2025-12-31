from django.db.models.signals import post_migrate
from django.dispatch import receiver

from orders.models import StatusOrder, PaymentMethod, ShipmentMethod

import logging
logger = logging.getLogger(__name__)

def load_data(model_class, data, table_name='', unique_field='name'):
    """
    Carga datos maestros usando get_or_create.
    """
    for item in data:
        lookup = {unique_field: item[unique_field]}
        m, _ = model_class.objects.get_or_create(
            **lookup,
            defaults=item
        )
        logger.debug("[TABLA = %s][Creando: %s]",
            table_name,
            m.name    
        )


@receiver(post_migrate)
def create_orders_defaults(sender, **kwargs):
    # Evita que se ejecute para otras apps
    if sender.name != 'orders':
        return

    # Datos a cargar
    data_order_status = [
        {'name': 'Cancelado', 'description': 'El envío fue cancelado.'},
        {'name': 'Pago a Confirmar', 'description': 'Se deberá confirmar el ingreso a la cuenta bancaria.'},
        {'name': 'Pago Confirmado', 'description': 'Una vez confirmado el pago.'},
        {'name': 'Pendiente de Retiro', 'description': 'Espera a ser retirado en Local.'},
        {'name': 'Preparando Envío', 'description': 'Tu pedido esta siendo preparado.'},
        {'name': 'En Camino', 'description': 'Tu pedido partió al domicilio indicado.'},
        {'name': 'Completado', 'description': 'Pedido Recibido.'},
        {'name': 'Devolución', 'description': 'Estado para pedidos devueltos.'},
        {'name': 'Rechazado', 'description': 'Rechazado por falta de Stock o Fraude.'},
    ]

    data_payment_methods = [
        {'name': 'Efectivo o Pago en Local', 
         'description': 'Completa el pago retirando por el local. (Solo entregas en el día)', 'is_active': True, 'time': 12},
        
        {'name': 'Transferencia Bancaria', 
         'description': 'Precio especial de contado por Transferencia directa.', 'is_active': True, 'time': 2},
        
        {'name': 'Tarjeta Crédito o Debito', 
         'description': 'Consultar promociones con tarjeta.', 'is_active': False, 'time': 2},
        
        {'name': 'USD Theter', 
         'description': 'Precios especiales por pago en criptomoneda.', 'is_active': False, 'time': 2},
    ]

    data_envio_methods = [
        {'name': 'Retiro en Local', 'description': 'Retiras en nuestro local', 'is_active': True, 'price': 0},
        
        {'name': 'Dentro de Circunvalación', 
         'description': 'Envío dentro del anillo de Córdoba', 'is_active': False, 'price': 1000.00},
        
        {'name': 'Fuera de Circunvalación', 
         'description': 'Envío fuera del anillo de Córdoba', 'is_active': False, 'price': 1500.00},
        
        {'name': 'Puntos de Retiro Correo', 
         'description': 'Envío para otras provincias', 'is_active': False, 'price': 3000.00},
    ]

    load_data(StatusOrder, data_order_status, 'StatusOrder')
    load_data(PaymentMethod, data_payment_methods, 'PaymentMethod')
    load_data(ShipmentMethod, data_envio_methods, 'ShipmentMethod')
