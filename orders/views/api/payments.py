from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from orders.models import PaymentMethod
from orders.serializers import PaymentSerializer

from core.permissions import IsAdminOrSuperUser
from core.utils.utils_basic import valid_id_or_None


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