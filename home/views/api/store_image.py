from rest_framework import status  
from rest_framework.views import APIView
from rest_framework.response import Response

# core app
from core.permissions import IsAdminOrSuperUser
from core.utils.utils_files import delete_physical_files_from_urls
from core.views.get_object_mixin import GetObjectMixin

from home.models import StoreImage
from home.services.store import StoreService
from home.serializers.store_image import StoreImageSerializer
from home.services.store_image import StoreImageService


class StoreImageAPI(APIView, GetObjectMixin):
    """
    API View for managing Store Images.
    Handles image creation, metadata updates, and physical file cleanup 
    with automatic succession logic for main images.
    """
    permission_classes = [IsAdminOrSuperUser]

    def delete(self, request, store_id: int | str, image_id: int | str) -> Response:
        """
        Deletes a store image record from the database.
        
        Business Logic:
        - If the deleted image was 'main', it promotes the next available image 
        via StoreImageService.
        
        Side Effects (via Signals):
        - Physical file cleanup: Managed by 'store_image_cleanup_file_on_delete' post_delete signal.
        - Cache invalidation: Managed by signals triggered upon record removal.
        """
        # 1. Fetch parent and target instance (raises 404 if not found)
        store = self._get_store(store_id=store_id)
        image = self._get_image(store_id=store.get('id'), image_id=image_id)
        image_type = image.image_type
        
        # Metadata for the extra_data in response
        extra_info = {
            "detail": f"Store Image Deleted - ID: {image_id}",
            "store_id": store.get('id')
        }
        
        # 2. Service Layer: Handles DB deletion and succession logic
        # The physical file cleanup is handled by post_delete signals via on_commit.
        next_main = StoreImageService.handle_delete(instance=image, store_id=store.get('id'))
        
        # 3. Response Enrichment: Inform the frontend if another image became 'Main'
        if next_main:
            extra_info['meta_updates'] = {
                "id": next_main.id,
                "main_image": next_main.main_image,
                "available": next_main.available,
                "image_type": next_main.image_type
            }
        else:
            # Useful for frontend to know they might need a placeholder
            extra_info['info'] = f"No more images left for type: {image_type}"
            
        return self.success_response(data=None, key="", **extra_info)


    def post(self, request, store_id: int | str) -> Response:
        """
        Creates a new image for a specific store.
        """
        store = self._get_store(store_id=store_id) # success or 400/404
        serializer = StoreImageSerializer(data=request.data, context={'store': store})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return self.success_response(
            key="store_image", data=serializer.data, 
            status_code=status.HTTP_201_CREATED
        )
    
    
    def patch(self, request, store_id: int | str, image_id: int | str) -> Response:
        """
        Partially updates an existing store image.

        Business Logic (via StoreImageService):
        - Atomic Succession: If 'main_image' status changes, promotes/demotes images.
        - Physical Cleanup: If 'image_url' is updated, the previous file is 
        deleted to prevent orphaned storage.

        Side Effects (via Signals):
        - Physical file cleanup: Managed by 'store_image_cleanup_file_on_update' post_delete signal.
        - Cache invalidation: Managed by signals triggered upon record removal.
        """
        # success or 400/404
        store = self._get_store(store_id=store_id)
        image = self._get_image(store_id=store.get('id'), image_id=image_id)
        
        serializer = StoreImageSerializer(
            image, 
            data=request.data, 
            partial=True, 
            context={'store': store}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return self.success_response(key='store_image', data=serializer.data)
    
    
    def get(self, request, store_id: int | str, image_id: int | str = None) -> Response:
        """
        Retrieves store images.
        Uses optimized .values() fetching to avoid model instantiation.
        """
        store = self._get_store(store_id=store_id)
        
        # CASE: Single Image Detail
        if image_id:
            image = self.get_from_service_or_error(
                obj_id=image_id,
                model_name='Store Image',
                service_call=lambda v_id: StoreImageService.get_images_api(
                    store_id=store.get('id'), pk=v_id
                )
            )
            return self.success_response(data=image, key='store_image')

        # CASE: List Images (Sorted by main image first)
        images = list(StoreImageService.get_images_api(store_id=store.get('id')))
    
        return self.success_response(data=images, key='store_images', count=len(images))
    
    # ----------------- Private Helpers -----------------
    
    def _get_image(self, store_id: int, image_id: int | str) -> StoreImage:
        """
        Ensures the image exists and belongs to the requested store.
        """
        return self.get_from_service_or_error(
            obj_id=image_id,
            model_name='Store Image',
            service_call=lambda v_id: StoreImage.objects.filter(id=v_id, store_id=store_id).first()
        )
    
    def _get_store(self, store_id: int | str) -> dict:
        """
        Retrieves store data from the service layer.
        """
        return self.get_from_service_or_error(
            obj_id=store_id,
            model_name='Store',
            service_call=lambda v_id: StoreService.get_public_store(v_id)
        )
    