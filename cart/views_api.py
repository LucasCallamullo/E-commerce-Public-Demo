

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.views import APIView
from rest_framework.response import Response

from cart.carrito import Carrito
from products.models import Product
from products.utils import valid_id_or_None    
from rest_framework.permissions import AllowAny


class CartAPIView(APIView):
    permission_classes = [AllowAny]  # Permite a cualquier usuario acceder a esta vista
    
    def post(self, request, product_id):
        quantity, cart_qty, action, response = self._valid_quantity_action(request)
        if response:
            return response
        
        product, response = self._get_product(product_id)
        if response:
            return response
        
        if action == 'add':
            # consulta disponibilidad del producto previo al paso del cart
            flag, _ = product.stock_or_available(quantity=quantity + cart_qty)
            if not flag:
                return Response({'detail': f"No hay suficiente stock de {product.name}."}, status=HTTP_400_BAD_REQUEST)
        
        # Recuperar carrito de la sesión del usuario, para actualizar en conjunto al diccionario
        # junto con el modelo cart en los metodos de la clase
        cart = Carrito(request)
        
        if action == 'add':
            cart.add_product(product=product, quantity=quantity)
            detail = "Producto agregado."
            
        elif action == 'substract':
            # quita productos del carrito, en caso de llegar a 0 lo elimina, mensajes basados en lo dicho
            delete_item = cart.subtract_product(product=product, quantity=quantity)
            detail = "Producto eliminado del carrito." if delete_item else "Producto eliminado del carrito"
        
        cart_context = cart.get_cart_serializer()
        return Response({'detail': detail, 'cart': cart_context}, status=HTTP_200_OK)
        
    def delete(self, request, product_id):
        action = request.data.get('action', '')
        if action != 'delete':
            return Response({'detail': "Acción invalida."}, status=HTTP_400_BAD_REQUEST)
        
        product, response = self._get_product(product_id)
        if response:
            return response
        
        cart = Carrito(request)
        
        flag = cart.delete_product(product=product)
        if not flag:
            return Response({'detail': "No esta el producto en el carrito.."}, status=HTTP_400_BAD_REQUEST)
        
        detail = 'Producto eliminado del carrito.'
        cart_context = cart.get_cart_serializer()
        return Response({'detail': detail, 'cart': cart_context}, status=HTTP_200_OK)
        
    def _get_product(self, product_id):
        product_id = valid_id_or_None(product_id)
        if not product_id:
            return None, Response({'detail': "Ingrese un ID válido."}, status=HTTP_400_BAD_REQUEST)
        try:
            product = ( 
                Product.objects
                .only('id', 'slug', 'name', 'price', 'main_image', 'stock', 'available')
                .get(id=product_id)
            )
            return product, None
        except Product.DoesNotExist:
            return None, Response({'detail': "El producto solicitado no existe."}, status=HTTP_404_NOT_FOUND)
        
    def _valid_quantity_action(self, request):
        action = request.data.get('action', '')
        action = action if action in ('add', 'substract', 'delete') else None
        
        quantity = valid_id_or_None(request.data.get('quantity', 1))
        
        cart_qty = valid_id_or_None(request.data.get('cart_quantity'))
        cart_qty = cart_qty if cart_qty else 0
        
        if None in (action, quantity):
            return None, None, None, Response({'detail': "Deja de boludear con los endpoints"}, status=HTTP_400_BAD_REQUEST)
        
        return quantity, cart_qty, action, None
   