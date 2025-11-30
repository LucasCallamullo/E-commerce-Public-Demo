

from cart.models import Cart

class CartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            cart_id = request.session.get('cart_id')

            if cart_id:
                # Cargar carrito por ID sin hacer un get_or_create
                try:
                    request.cart = Cart.objects.get(pk=cart_id)
                except Cart.DoesNotExist:
                    # Si el ID en sesión es inválido, creamos uno nuevo
                    request.cart = Cart.objects.create(user=request.user)
                    request.session['cart_id'] = request.cart.id
            else:
                # Primera vez que accede en la sesión → crear carrito y guardarlo
                cart, _ = Cart.objects.get_or_create(user=request.user)
                request.cart = cart
                request.session['cart_id'] = cart.id
        else:
            request.cart = None

        return self.get_response(request)
    
    
"""  
class CartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # DB Cart
            cart, _ = Cart.objects.get_or_create(user=request.user)
            request.cart = cart
        else:
            # Session Cart
            request.cart = None

        return self.get_response(request)
"""