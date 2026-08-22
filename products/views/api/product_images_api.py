from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError, ParseError
# services
from products.models.product import Product
from products.services.product_images import ProductImageService
# core app
from core.views.get_object_mixin import GetObjectMixin
from core.permissions import IsAdminOrSuperUser
from core.utils.utils_parsers import valid_id_or_None


class ProductImagesView(APIView, GetObjectMixin):
    """
    API View to manage Product Image assets.
    Handles bulk creation, batch deletion, and optimized retrieval.
    """
    
    def get_permissions(self):
        """
        Dynamically assigns permissions:
        - POST, DELETE, PUT, PATCH: Restricted to Admin/SuperUser.
        - GET: Public access (AllowAny).
        """
        # GET es lectura pública
        if self.request.method == 'GET':
            return [AllowAny()]
        # POST, DELETE, PUT, PATCH son escritura protegida
        return [IsAdminOrSuperUser()]
    
    
    def post(self, request, product_id: int | str) -> Response:
        """
        Associates a batch of image URLs with a Product.
        
        If the product has no main image, the first URL in the list 
        is automatically promoted to 'main_image=True' via Service logic.
        """
        # 1. Get URLs from request
        urls = request.data.get("images_urls", [])
        if not urls:
            raise ValidationError(detail="No image URLs provided. A non-empty list is required.")
        
        # 2. Get instance or raises 400/404
        product = self._get_product(product_id=product_id)

        # 3. Delegate bulk creation logic to Service
        result = ProductImageService.bulk_create_images(product=product, urls=urls)
        
        # Use 207 Multi-Status for batch operations if multiple URLs are sent
        res_status = status.HTTP_201_CREATED if len(urls) == 1 else status.HTTP_207_MULTI_STATUS
        
        return self.success_response(
            key="product_id", data=product_id, 
            status_code=res_status,
            **result
        )
    
    def delete(self, request, product_id: int | str) -> Response:
        """
        Removes multiple images and triggers main_image redistribution logic.
        """
        delete_images = request.data.get("delete_images", [])
        
        # 1. Body Validation: Raise instead of return
        if not isinstance(delete_images, list):
            raise ParseError(detail="Invalid format: delete_images must be a list")
            
        # 2. Extract and validate IDs
        valid_image_ids = {int(i) for i in delete_images if valid_id_or_None(i)}
        if not valid_image_ids:
            raise ValidationError(detail="No valid image IDs provided for deletion.")
            
        # 3. Get instance or raises 400/404
        product = self._get_product(product_id=product_id)

        # 4. Delegate succession and deletion logic to Service
        result = ProductImageService.delete_images_and_update_main(
            product=product, 
            image_ids=valid_image_ids
        )

        return self.success_response(key="product_id", data=product_id, **result)
    
    def get(self, request, product_id: int | str) -> Response:
        """
        Retrieves image URLs for a specific product.
        """
        # 2. Fast existence check using Mixin (Optimized: only fetch 'id'), get dict or raise 404
        product = self.get_values_or_error(
            model_class=Product, 
            obj_id=product_id, 
            values=('id',) # Note: comma for single-item tuple
        )
        
        images = ProductImageService.get_list_urls(product_id=product.get('id'))
        
        return self.success_response(
            key='images',
            data=images,
            count=len(images)
        )
    
    # --------------------- Private helpers -
    
    def _get_product(self, product_id: int | str) -> Product:
        """
        Retrieves a Product instance or raises a 400 (Invalid ID) or 404 (Not Found) error.
        
        Optimized via 'select_only' to fetch only required fields for image management,
        reducing database overhead.
        """
        return self.get_instance_or_error(
            model_class=Product, 
            obj_id=product_id, 
            select_only=('id', 'main_image')
        )
        
    """
    # 1 - Sobreescribir metodos para aplicar distintos parsers/permissions segun la peticion http
    def get_parsers(self):
        If the method is POST, it returns MultiPartParser to allow file uploads
        For (GET, DELETE), it uses the default parsers defined in the base class or DRF settings.
        
        # Si self.request no existe (como durante la generación del esquema),
        # retorna los parsers por defecto.
        if self.request is None or self.request.method == 'POST':
            return [MultiPartParser()]    # Parser para recibir archivos
        return super().get_parsers()
    """
