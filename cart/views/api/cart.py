from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from cart.carrito import Carrito
from products.models.product import Product

from core.utils.utils_basic import valid_id_or_None    

from rest_framework.exceptions import NotFound, ValidationError

class CartAPIView(APIView):
    """
    API view for managing cart actions (add, subtract) for a product.

    Permissions:
        AllowAny - any user (authenticated or anonymous) can access this endpoint.

    Methods:
        post(request, product_id): Handles cart modifications based on the action
        specified in the request data.
    """
    permission_classes = [AllowAny]  # Allow any user to access this view
    
    def post(self, request, product_id):
        """
        Handles POST requests to modify the cart.

        Request data:
            action (str): "add" or "substract" (required)
            quantity (int, optional): Number of items to add/subtract (default=1)
            cart_quantity (int, optional): Current quantity of the product in the cart

        Returns:
            Response: JSON response containing success status, detail message, 
            and updated cart data.
        """

        # 1. Extract requested action and quantities from request
        action = request.data.get('action', '')
        quantity = valid_id_or_None(id_value=request.data.get('quantity', 1))
        cart_qty = valid_id_or_None(
            id_value=request.data.get('cart_quantity', 0),
            allow_zero=True
        )

        if quantity is None or action not in ('add', 'subtract'):
            return Response(
                {
                    'detail': "Cart data missing or invalid.",
                    'success': False
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Retrieve the product instance or raise an error
        product = self._get_product(product_id)

        # 3. Initialize the session cart object to synchronize with DB
        cart_session = Carrito(request)
        
        # Handle "add" action
        if action == 'add':
            # Check if requested quantity is available in stock
            is_available, _ = product.stock_or_available(quantity=quantity + cart_qty)
            if not is_available:
                return Response(
                    {
                        'success': False,
                        'detail': f"No hay suficiente stock de {product.name}."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cart_session.add_product(product=product, quantity=quantity)
            detail = "Producto agregado."

        # Handle "subtract" action
        elif action == 'subtract':
            action_item = cart_session.subtract_product(product=product, quantity=quantity)

            if action_item == 'patch':
                detail = "Producto actualizado en el carrito."
            elif action_item == 'delete':
                detail = "Producto eliminado del carrito."
            else:  # 'not_found'
                return Response(
                    {'detail': "Product not found in cart.", 'success': False},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Return success response with updated cart snapshot
        return Response(
            {
                'success': True,
                'detail': detail,
                'cart': cart_session.get_cart_serializer()
            },
            status=status.HTTP_200_OK
        )
        
    
    def delete(self, request, product_id):
        """
        Handles DELETE requests to remove a product from the cart.

        Request data:
            action (str): Must be 'delete'. Any other value is considered invalid.

        Args:
            request (Request): DRF request object.
            product_id (int | str): ID of the product to remove.

        Returns:
            Response: JSON response with success status, detail message, and
                    the updated cart data.
        """
        # 1. Validate action
        action = request.data.get('action', '')
        if action != 'delete':
            return Response(
                {'detail': "Invalid Action.", 'success': False}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 2. Retrieve product instance
        product = self._get_product(product_id)  
        
        # 3. Initialize session cart
        cart_session = Carrito(request)
        
        # 4. Remove product from cart
        flag = cart_session.delete_product(product=product)
        if flag != 'delete':
            return Response(
                {'detail': "Product not found in cart.", 'success': False}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 5. Return success response with updated cart
        return Response(
            {
                'success': True,
                'detail': 'Producto eliminado del carrito.', 
                'cart': cart_session.get_cart_serializer()
            }, 
            status=status.HTTP_200_OK
        )

    def get(self, request):
        # Para usuarios anónimos podrías crear un carrito de sesión
        cart_session = Carrito(request)  
        return Response(
            {
                "cart": cart_session.get_cart_serializer(),
                "success": True,
            },
            status=status.HTTP_200_OK
        )

    def _get_product(self, product_id: int) -> Product:
        """
        Resolve and validate a Product instance from a given product ID.

        Design notes:
        - Exceptions raised here are automatically handled by DRF and
        formatted by the global custom_exception_handler.

        Args:
            product_id (int|Any): Raw product identifier from the request
                            (URL or payload).

        Returns:
            Product: A valid Product instance.

        Raises:
            ValidationError(HTTP 400): If the provided product ID is invalid.
            NotFound(HTTP 404): If the product does not exist in the database.
        """
        product_id = valid_id_or_None(product_id)
        if not product_id:
            raise ValidationError("ID de producto inválido")

        try:
            return (
                Product.objects
                .only(
                    'id', 'slug', 'name', 'price',
                    'main_image', 'stock', 'available'
                )
                .get(id=product_id)
            )
        except Product.DoesNotExist:
            raise NotFound("El producto solicitado no existe")

