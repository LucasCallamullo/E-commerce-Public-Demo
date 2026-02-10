from rest_framework.views import APIView
from rest_framework.response import Response  
# core app
from core.permissions import IsAdminOrSuperUser
from core.views.get_object_mixin import GetObjectMixin

from home.models import Store
from home.serializers.store import StoreSerializer


class StoreAPI(APIView, GetObjectMixin):
    permission_classes = [IsAdminOrSuperUser]
    
    def patch(self, request, pk: int | str) -> Response:
        # Retrieve model instance (or raise 400/404)
        store = self._get_store(store_id=pk)
        
        # Validate and persist changes
        serializer = StoreSerializer(store, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return self.success_response(data=serializer.data, key='store')
    
    def get(self, request, pk: int | str = None) -> Response:
        """
        Retrieves payment methods.
        
        If 'pk' is provided: Returns a single object as a dictionary.
        If 'pk' is None: Returns a list of all payment methods.
        """
        if pk:
            # Use Mixin to retrieve a specific record as a dict (DB optimized)
            store = self.get_values_or_error(Store, pk)
            return self.success_response(data=store, key="store")
        
        # Retrieve all records as a list of dictionaries to bypass model instantiation overhead
        stores = list(Store.objects.all().values())
        return self.success_response(
            data=stores,
            key="stores",
            count=len(stores)
        )
    
    # ----------------- private helpers
    def _get_store(self, store_id: int|str) -> Store:
        return self.get_instance_or_error(
            model_class=Store,
            obj_id=store_id
        )
    
