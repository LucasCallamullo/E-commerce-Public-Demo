

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated



from orders.serializers import OrderFormSerializer, ShipmentSerializer, PaymentSerializer
from orders.models import ShipmentMethod, PaymentMethod

from users.permissions import IsAdminOrSuperUser
from products.utils import valid_id_or_None



class PaymentAPI(APIView):
    # Verificar si es role == 'admin' o user.id == 1
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    
    def patch(self, request, payment_id):
        payment_id = valid_id_or_None(payment_id)
        if not payment_id:
            return Response({"success": False, "detail": 'Payment ID Incorrect.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            payment = PaymentMethod.objects.get(id=payment_id)
        except PaymentMethod.DoesNotExist:
            return Response({"success": False, "detail": "método de pago no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        # mandar a validar con el serializador el json recibido desde el form
        serializer = PaymentSerializer(payment, data=request.data, partial=True)

        # si esta todo bien se guarda el objeto automaticamente
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "message": "Método de pago actualizado."}, status=status.HTTP_200_OK)
        
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        
class ShipmentAPI(APIView):
    # Verificar si es role == 'admin' o user.id == 1
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    
    def patch(self, request, shipment_id):
        
        shipment_id = valid_id_or_None(shipment_id)
        if not shipment_id:
            return Response({"success": False, "detail": 'Shipment ID Incorrect.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            shipment = ShipmentMethod.objects.get(id=shipment_id)
        except ShipmentMethod.DoesNotExist:
            return Response({"success": False, "detail": "Método de envío no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        # validar con el serializador el json recibido desde el form
        serializer = ShipmentSerializer(shipment, data=request.data, partial=True)

        # si esta todo bien se guarda el objeto automaticamente
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "message": "Shipment actualizado correctamente"}, status=status.HTTP_200_OK)
            
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


from orders import utils  
from cart.models import Cart, CartItem
class OrderAPI(APIView):
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados pueden acceder
    
    def post(self, request):
        # print(request.data)  # for debug # Para ver qué datos realmente llegan
        serializer = OrderFormSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Confirmar pedido y hacer reserva de stock:
        cart = request.cart
        dict_p_q, response = utils.confirm_stock_availability(cart)
        if not dict_p_q:
            return response
        
        # recuperamos el json de Datos ya validados
        user = request.user
        order_data = serializer.validated_data
        order, response = utils.create_order_pending(
            order_data, user, dict_p_q['products'], dict_p_q['quantities']
        )
        if not order:
            return response
            
        return Response({'order_id': order.id}, status=status.HTTP_201_CREATED)
        
