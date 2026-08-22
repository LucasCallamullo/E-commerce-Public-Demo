from typing import Any
from rest_framework.views import APIView
from rest_framework.response import Response

# core app
from core.permissions import IsAdminOrSuperUser
from core.views.get_object_mixin import GetObjectMixin

# home app
from home.models.social_media import SocialMedia
from home.services.store import StoreService
from home.services.social_media import SocialMediaService
from home.serializers.social_media import SocialMediaSerializer


class SocialMediaAPI(APIView, GetObjectMixin):
    """
    API View to handle Social Media networks linked to a Store.
    Implements optimized service-based retrieval and standardized response formatting.
    """

    def get_permissions(self):
        """
        Dynamically assigns permissions based on the HTTP method.
        Only Admins or Superusers can modify social media data.
        """
        # from rest_framework.permissions import AllowAny
        # if self.request.method in ('GET'):
        #    return [AllowAny()]
        # 'PUT', 'PATCH', 'POST', 'DELETE'
        return [IsAdminOrSuperUser()]
    
    def patch(self, request, store_id: int | str, network_id: int | str) -> Response:
        """
        Partially updates an existing social media network.
        
        1. Validates the Store exists and retrieves its basic data.
        2. Retrieves the specific SocialMedia instance owned by the store.
        3. Updates data via SocialMediaSerializer using optimized persistence.
        """
        # Retrieve store dict (or raise 400/404)
        store = self._get_store(store_id=store_id)
        
        # Retrieve model instance (or raise 400/404)
        net_instance = self._get_social_media(
            store_id=store.get('id'), 
            network_id=network_id
        )
        
        serializer = SocialMediaSerializer(
            net_instance, 
            data=request.data, 
            partial=True, 
            context={'store': store}
        )
        
        # Validate and persist changes
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return self.success_response(data=serializer.data, key='social_network')

    def get(self, request, store_id: int | str, network_id: int | str = None) -> Response:
        """
        Retrieves social media data.
        
        If 'network_id' is provided: Returns detailed info for a single network.
        If 'network_id' is None: Returns the dashboard list for the store.
        """
        # Validate store_id and get the cleaned ID
        store = self._get_store(store_id=store_id)
        valid_store_id = store.get('id')
        
        # CASE: List all social networks for the store
        if not network_id:
            networks = SocialMediaService.get_dashboard_list(store_id=valid_store_id)
            return self.success_response(
                data=networks, 
                key='social_networks', 
                count=len(networks)
            )
        
        # CASE: Detail for a single network via Service
        net_details = self.get_from_service_or_error(
            obj_id=network_id,
            model_name='Social Network',
            service_call=lambda v_id: SocialMediaService.get_details_by_id(
                network_id=v_id, 
                store_id=valid_store_id
            )
        )
        return self.success_response(data=net_details, key='social_network')

    # ----------------- Private Helpers -----------------

    def _get_social_media(self, store_id: int, network_id: int | str) -> SocialMedia:
        """
        Retrieves a SocialMedia model instance through the service layer.
        Ensures the network belongs to the specified store.
        """
        return self.get_from_service_or_error(
            obj_id=network_id,
            model_name='Social Network',
            service_call=lambda v_id: (
                SocialMediaService.get_instance_by_id(network_id=v_id, store_id=store_id)
            )
        )

    def _get_store(self, store_id: int | str) -> dict[str, Any]:
        """
        Retrieves store data or raises an error if the store does not exist.
        Used for cross-checking ownership and validation context.
        """
        return self.get_from_service_or_error(
            obj_id=store_id,
            model_name='Store',
            service_call=lambda v_id: StoreService.get_public_store(v_id)
        )
        