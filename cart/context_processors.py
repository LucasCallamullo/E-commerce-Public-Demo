import json
from cart.carrito import Carrito


def cart_context(request):
    cart_session = Carrito(request)
    return {
        'cart_data': cart_session.get_cart_serializer()
    }

