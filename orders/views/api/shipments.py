from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from orders.models import ShipmentMethod
from orders.serializers import ShipmentSerializer

from core.permissions import IsAdminOrSuperUser
from core.utils.utils_basic import valid_id_or_None


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
