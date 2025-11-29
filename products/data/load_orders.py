

from orders.models import StatusOrder, PaymentMethod, ShipmentMethod

def load_data(model_class, data):
    """
    Carga datos en un modelo de Django usando get_or_create.

    Args:
        model_class (Model): Clase del modelo en el que se cargarán los datos.
        data (list): Lista de diccionarios con los datos a cargar.
    """
    for item in data:
        objeto, created = model_class.objects.get_or_create(**item)
        if created:
            print(f'Se creó correctamente: {objeto}')
        else:
            print(f'Ya existía: {objeto}')


def load_orders_init():
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
        {'name': 'Efectivo o Pago en Local', 'description': 'Completa el pago retirando por el local. (Solo entregas en el día)', 'is_active': True, 'time': 12},
        {'name': 'Transferencia Bancaria', 'description': 'Precio especial de contado por Transferencia directa.', 'is_active': True, 'time': 2},
        {'name': 'Tarjeta Crédito o Debito', 'description': 'Consultar promociones con tarjeta.', 'is_active': False, 'time': 2},
        {'name': 'USD Theter', 'description': 'Precios especiales por pago en criptomoneda.', 'is_active': False, 'time': 2},
    ]

    data_envio_methods = [
        {'name': 'Retiro en Local', 'description': 'Retiras en nuestro local', 'is_active': True, 'price': 0},
        {'name': 'Dentro de Circunvalación', 'description': 'Envío dentro del anillo de Córdoba', 'is_active': False, 'price': 1000.00},
        {'name': 'Fuera de Circunvalación', 'description': 'Envío fuera del anillo de Córdoba', 'is_active': False, 'price': 1500.00},
        {'name': 'Puntos de Retiro Correo', 'description': 'Envío para otras provincias', 'is_active': False, 'price': 3000.00},
    ]

    # Llamadas a la función genérica
    load_data(StatusOrder, data_order_status)
    load_data(PaymentMethod, data_payment_methods)
    load_data(ShipmentMethod, data_envio_methods)


if __name__ == "__main__":
    load_orders_init()
