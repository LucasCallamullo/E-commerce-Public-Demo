from rest_framework.views import APIView
from rest_framework.response import Response
# core app
from core.permissions import IsAdminOrSuperUser
from core.views.get_object_mixin import GetObjectMixin
# orders app
from orders.models import ShipmentMethod
from orders.serializers.methods import ShipmentSerializer

class ShipmentAPI(APIView, GetObjectMixin):
    """
    API View to manage Shipment Methods.
    Provides optimized retrieval (GET) and partial updates (PATCH) 
    with standardized response formatting.
    """
    permission_classes = [IsAdminOrSuperUser]
    
    def patch(self, request, pk: int | str) -> Response:
        """
        Partially updates a specific shipment method.
        
        1. Retrieves the model instance using GetObjectMixin.
        2. Validates incoming JSON data via ShipmentSerializer.
        3. Persists changes using optimized SQL updates.
        """
        shipment = self._get_shipment_method(shipment_id=pk)
        
        # Initialize serializer with partial=True for PATCH operations
        serializer = ShipmentSerializer(shipment, data=request.data, partial=True)

        # Delegate validation and error raising to the serializer
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return self.success_response(data=serializer.data, key='shipment_method')

    def get(self, request, pk: int | str = None) -> Response:
        """
        Retrieves shipment methods.
        
        If 'pk' is provided: Returns a single object as a dictionary.
        If 'pk' is None: Returns a list of all shipment methods.
        """
        if pk:
            # Use Mixin to retrieve a specific record as a dict (DB optimized)
            ship = self.get_values_or_error(ShipmentMethod, pk)
            return self.success_response(data=ship, key="shipment_method")
        
        # Retrieve all records as a list of dictionaries to bypass model instantiation overhead
        shipments = list(ShipmentMethod.objects.all().values())
        return self.success_response(
            data=shipments,
            key="shipment_methods",
            count=len(shipments)
        )
        
    def _get_shipment_method(self, shipment_id: int | str) -> ShipmentMethod:
        """
        Internal helper to fetch a ShipmentMethod instance or raise a 404/400 error.
        """
        return self.get_instance_or_error(
            model_class=ShipmentMethod,
            obj_id=shipment_id
        )
