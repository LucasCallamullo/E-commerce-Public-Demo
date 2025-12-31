

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from cart.carrito import Carrito
from orders.serializers import OrderFormSerializer
from orders import utils
from orders.services.orders import OrderService  


class OrderAPI(APIView):
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados pueden acceder
    # para rate limit 3/min
    throttle_scope = 'orders'
    
    
    def post(self, request):
        # print(request.data)  # for debug # Para ver qué datos realmente llegan
        serializer = OrderFormSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        order = OrderService.create_order_pending(
            user=request.user,
            order_data=serializer.validated_data
        )
        
        # capaz agregar dependencia a cart inevvitable para limpiar post procesamiento
        cart_session = Carrito(request)
        cart_session.clear()
        
        # retornamos unicamente el id, para construir la url de redirect en front 
        # aunque capaz sería mejor devolver la url no lo sé, de momento esta asi
        return Response({'order_id': order.id}, status=status.HTTP_201_CREATED)
        