from cart.models import Cart


class CartMiddleware:
    """
    CartMiddleware is responsible for resolving the current user's cart
    once per request and attaching it to the request object.

    Key ideas:
    - This middleware does NOT replace the database.
    - It performs at most ONE database lookup per request.
    - The resolved cart is stored in memory as `request.cart`
      and can be reused by views, services, APIs, and templates.

    Why this exists:
    - Avoid duplicating cart-loading logic across multiple views.
    - Provide a single, consistent way to access the cart.
    - Ensure all parts of the request lifecycle use the same cart instance.

    Scope:
    - The cart lives only for the duration of the request (request-scoped state).
    - It is NOT a cross-request cache.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Resolve and attach the cart to the request.

        Behavior:
        - If the user is authenticated:
            - Try to load the cart using the ID stored in the session.
            - If the session ID is invalid, create a new cart.
            - If no cart ID exists in the session, create or reuse
              the user's cart and store its ID in the session.
        - If the user is not authenticated:
            - No cart is attached to the request.

        After this middleware runs:
        - `request.cart` is always available (either a Cart instance or None).
        - No further database lookups are required to access the cart
          during this request.
        """
        user = request.user
        if not user.is_authenticated:
            # Anonymous users do not have a cart attached at the request level.
            request.cart = None
            return self.get_response(request)
        
        # recupera de la session previamente guardado "cart_id"
        cart_id = request.session.get("cart_id")
        
        if not cart_id:
            # First access in this session:
            # Either reuse an existing cart for the user or create a new one.
            cart, _ = Cart.objects.get_or_create(user=user)
            request.cart = cart
            request.session["cart_id"] = cart.id
            
            return self.get_response(request)
            
            
        # Load the cart from the database using the session ID.
        # This avoids calling get_or_create on every request.
        try:
            request.cart = Cart.objects.get(pk=cart_id)
        except Cart.DoesNotExist:
            # The session contains an invalid cart ID (deleted or corrupted).
            # Create a new cart and store its ID back in the session.
            request.cart = Cart.objects.create(user=user)
            request.session["cart_id"] = request.cart.id

        return self.get_response(request)

