from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser

from products.models.product_image import ProductImage
from products.models.product import Product

from core.permissions import IsAdminOrSuperUser
from core.utils.utils_basic import valid_id_or_None
from core.utils.utils_image import get_url_from_imgbb



class ProductImagesView(APIView):
    
    # 1 - Sobreescribir metodos para aplicar distintos parsers/permissions segun la peticion http
    def get_parsers(self):
        """If the method is POST, it returns MultiPartParser to allow file uploads
        For (GET, DELETE), it uses the default parsers defined in the base class or DRF settings."""
        
        # Si self.request no existe (como durante la generación del esquema),
        # retorna los parsers por defecto.
        if self.request is None or self.request.method == 'POST':
            return [MultiPartParser()]    # Parser para recibir archivos
        return super().get_parsers()
    
    def get_permissions(self):
        """Permisos estrictos para POST/DELETE, abierto para otros"""
        if self.request.method in ('POST', 'DELETE'):
            return [IsAdminOrSuperUser()]    # Permissions custom en user.permissions
        return [AllowAny()]
    
    def post(self, request, product_id):
        product, error = self._get_product(product_id)
        if error:
            return error

        images = ProductImage.objects.filter(product=product)
        
        # 3. Procesar imágenes
        uploaded_urls = []
        errors = []
        has_main = any(img.main_image for img in images)    # return True or False
        
        for img in request.FILES.getlist('images'):
            try:
                url = get_url_from_imgbb(img)  # Validaciones de ImgBB and return img_url
                
                # la logica es se guarda como True si no tenía main images
                ProductImage.objects.create(product=product, image_url=url, main_image=not has_main)
                
                # Si no hay otra imagen marcada como principal, esta se marca como main con metodo del modelo
                if not has_main:
                    product.update_main_image(url=url) 
                    has_main = True
                
                uploaded_urls.append(url)
                
            # si get_url_from_imgbb devolviera algun problema lo almacenamos para mostrar despues
            except ValueError as e:
                errors.append(f"{img.name}: {str(e)}")
                continue
            except Exception as e:
                errors.append(f"{img.name}: Error inesperado - {str(e)}")
                continue

        # 3. Construir respuesta
        response_data = {
            "success": True if uploaded_urls else False,
            "uploaded_images": uploaded_urls,
            "errors": errors if errors else None,
            "total_uploaded": len(uploaded_urls)
        }
        
        print(response_data)

        return Response(response_data, status=status.HTTP_201_CREATED if uploaded_urls else status.HTTP_207_MULTI_STATUS)
        
    def delete(self, request, product_id):
        # 1. Validación de imágenes a eliminar
        delete_images = request.data.get("delete_images", [])
        if not isinstance(delete_images, list):
            return Response(
                {"detail": "Formato inválido: delete_images debe ser una lista"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 2. Filtrar solo los IDs válidos
        valid_image_ids = {int(i) for i in delete_images if valid_id_or_None(i)}
        if not valid_image_ids:
            return Response({"detail": "Ningún ID de imagen válido para eliminar."}, status=status.HTTP_400_BAD_REQUEST)
        
        # 3. Verificación de existencia (consulta a DB sólo si el ID es válido)
        product, error = self._get_product(product_id)
        if error:
            return error
                
        # 5. Verificar si se elimina la imagen principal
        main_images_to_delete = ProductImage.objects.filter(
            id__in=valid_image_ids,
            product=product,
            main_image=True
        ).exists()

        # 6. Eliminación en batch
        deleted_count, _ = ProductImage.objects.filter(
            id__in=valid_image_ids,
            product=product
        ).delete()
        
        # 7. Actualizar imagen principal si es necesario
        if main_images_to_delete and deleted_count > 0:
            new_main_image = (
                ProductImage.objects
                .filter(product=product)
                .exclude(id__in=valid_image_ids)
                .order_by('id')
                .first()
            )
            
            new_main_url = new_main_image.image_url if new_main_image else None
            product.update_main_image(new_main_url)
        
        return Response({
                "success": True,
                "deleted_count": deleted_count,
                "main_image_updated": main_images_to_delete,
                "new_main_image": new_main_url if main_images_to_delete else None
            }, 
            status=status.HTTP_200_OK
        )
    
    def get(self, request, product_id):
        # some endpoints need all info from images
        extra_data = request.query_params.get('all') == 'true'
        
        product, error = self._get_product(product_id, extra_data=extra_data)
        if error:
            return error
        
        # some endpoints need all info from images
        if extra_data:
            images = ( 
                ProductImage.objects.filter(product=product)
                .values('image_url', 'id').order_by('-main_image')
            )
        else:
            images = ( 
                ProductImage.objects.filter(product=product, main_image=False)
                .values_list('image_url', flat=True)
            )
            
        response = {
            'images': images,
            'count': len(images)
        }
        
        if extra_data:
            response['product'] = {'id': product.id, 'description': product.description}

        return Response(response, status=status.HTTP_200_OK)
        
    def _get_product(self, product_id, extra_data=False):
        # 1. Validar datos de entrada
        product_id = valid_id_or_None(product_id) 
        if not product_id:
            return None, Response({"detail": "Se requiere el ID del producto"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Verificación de existencia (consulta a DB sólo si el ID es válido)
        try:
            values = ('id', 'main_image') if not extra_data else ('id', 'description')
            product = (Product.objects.only(*values).get(id=product_id))
            return product, None
        except Product.DoesNotExist:
            return None, Response({"success": False, "detail": "No existe el producto."}, status=status.HTTP_404_NOT_FOUND)