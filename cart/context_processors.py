

import json
from cart.carrito import Carrito


def carrito_total(request):
    """
    Notes:
        Al pasar el total ya calculado, no necesita que el renderizado recalcule cada vez el valor cuando lo paso
        esto debería mejorar el rendimiento de la app
        
        - 'cart': list of cart items (each is a dict)
        - 'cart_price': total price (float)
        - 'cart_quantity': total items (int)
    """
    cart = Carrito(request)
    context = cart.get_cart_serializer()
    
    return {'cart_data': json.dumps(context)}

"""
    context = {
        'carrito': carrito,
        'total_price': carrito.total_price,
        'total_items': carrito.total_items,
    }
    """