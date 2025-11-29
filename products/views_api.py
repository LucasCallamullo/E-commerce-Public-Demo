

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from django.db.models import F

# views.py
from products import filters, utils
from products.models import Product, PCategory, PSubcategory, PBrand, ProductImage
from products.serializers import (
    ProductSerializer, PCategorySerializer, PSubcategorySerializer, PBrandSerializer,
    ProductListSerializer
)
from users.permissions import IsAdminOrSuperUser

from favorites.utils import get_favs_products

class ProductAPIView(APIView):
    
    def get_permissions(self):
        """Permisos estrictos para GET abierto para otros"""
        if self.request.method in ('GET'):
            return [AllowAny()]
        
        # 1. Verificar si es role == 'admin' o user.id == 1
        return [IsAdminOrSuperUser()]    # Permissions custom en user.permissions
        
    def get(self, request, product_id=None):
        
        if product_id:
            pass
        
        else:
            user = request.user
            favorites_ids = get_favs_products(user)
            context = filters.get_context_filtered_products(request)
            products = (
                context['products'].values(*filters.VALUES_CARDS_LIST)
                .order_by('price', 'id').annotate(
                    category_id=F("category__id"),
                    subcategory_id=F("subcategory__id"),
                    brand_id=F("brand__id"),
                )
            )
            
            # Serializar los productos de la página actual    page.object_list
            page_num = request.GET.get('page')
            products_page, pagination = filters.get_paginator(products=products, page_num=page_num, quantity=100)
            context['pagination'] = pagination
            
            serializer = ProductListSerializer(products_page, many=True, context={'favorites_ids': favorites_ids})
            context['products'] = serializer.data

            return Response(context, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ProductSerializer(data=request.data, context={'user': request.user})
        
        if serializer.is_valid():
            product = serializer.save()
            return Response({"success": True, "product_id": product.id}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, product_id):
        product_id = utils.valid_id_or_None(product_id)
        if not product_id:
            return Response({"detail": "ID inválido: debe ser un número positivo"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Verificación de existencia (consulta a DB sólo si el ID es válido)
        try:
            product = (
                Product.objects
                .select_related('category', 'subcategory', 'brand')
                .only(*filters.PRODUCT_FIELDS_UPDATE) 
                .get(id=product_id)
            )
        except Product.DoesNotExist:
            return Response({"success": False, "detail": "No existe el producto."}, status=status.HTTP_404_NOT_FOUND)
        
        images = ProductImage.objects.filter(product=product)
        
        # 4. Pasamos al serializer el objeto, la data/json(body), y actualizacion parcial de campos
        serializer = ProductSerializer(
            product, data=request.data, partial=True, 
            context={
                'user': request.user,
                'images': images
            }
        )
        
        # 5. Verifica el formulario sino retorna algunos de los raise serializers.ValidationError
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        # 6. aca DRF llama internamente a update(instance, validated_data)
        serializer.save()
        return Response({"success": True, "product_id": product_id}, status=status.HTTP_200_OK)
    

class ProductImagesView(APIView):
    
    # 1 - Sobreescribir metodos para aplicar distintos parsers/permissions segun la peticion http
    def get_parsers(self):
        """If the method is POST, it returns MultiPartParser to allow file uploads
        For (GET, DELETE), it uses the default parsers defined in the base class or DRF settings."""
        if self.request.method == 'POST':
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
                url = utils.get_url_from_imgbb(img)  # Validaciones de ImgBB and return img_url
                
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
        valid_image_ids = {int(i) for i in delete_images if utils.valid_id_or_None(i)}
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
        
        response_data = {
            "success": True,
            "deleted_count": deleted_count,
            "main_image_updated": main_images_to_delete,
            "new_main_image": new_main_url if main_images_to_delete else None
        }
        return Response(response_data, status=status.HTTP_200_OK)
    
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
        product_id = utils.valid_id_or_None(product_id) 
        if not product_id:
            return None, Response({"detail": "Se requiere el ID del producto"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Verificación de existencia (consulta a DB sólo si el ID es válido)
        try:
            values = ('id', 'main_image') if not extra_data else ('id', 'description')
            product = (Product.objects.only(*values).get(id=product_id))
            return product, None
        except Product.DoesNotExist:
            return None, Response({"success": False, "detail": "No existe el producto."}, status=status.HTTP_404_NOT_FOUND)
        

class BaseProductAPIView(APIView):
    # Estos atributos DEBEN ser definidos en las clases hijas
    serializer_class = None
    model = None
    cache_key = None  # Clave para el caché (opcional)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        instance = serializer.save()
        self._invalidate_cache()  # Limpia caché si es necesario
        return Response({"success": True, "id": instance.id}, status=status.HTTP_201_CREATED)

    def put(self, request, obj_id):
        instance, error = self._get_instance_model(obj_id=obj_id)
        if error:
            return error
        
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        self._invalidate_cache()
        return Response({"success": True, "id": instance.id}, status=status.HTTP_200_OK)
    
    def delete(self, request, obj_id):
        instance, error = self._get_instance_model(obj_id=obj_id)
        if error:
            return error
        instance.delete()
        self._invalidate_cache()
        return Response({"success": True, "detail": "model deleted"}, status=status.HTTP_200_OK)
        
    def _get_instance_model(self, obj_id):
        obj_id = utils.valid_id_or_None(obj_id)
        if not obj_id:
            return None, Response({"detail": "ID inválido"}, status=status.HTTP_400_BAD_REQUEST)
        try: 
            instance = self.model.objects.get(id=obj_id)
        except self.model.DoesNotExist:
            return None, Response({'detail': 'Model not found'}, status=status.HTTP_404_NOT_FOUND)
        if getattr(instance, 'is_default', False):    # si por algun motivo es el por defecto
            return None, Response({"detail": "No se puede modificar un registro por defecto."}, status=status.HTTP_403_FORBIDDEN)
        return instance, None
        
    def _invalidate_cache(self):
        if self.cache_key:
            cache.delete(self.cache_key)
            

class PCategoryAPIView(BaseProductAPIView):
    permission_classes = [IsAdminOrSuperUser]
    serializer_class = PCategorySerializer
    model = PCategory
    cache_key = 'categories_dropmenu'
    

class PSubcategoryAPIView(BaseProductAPIView):
    permission_classes = [IsAdminOrSuperUser]
    serializer_class = PSubcategorySerializer
    model = PSubcategory
    cache_key = 'categories_dropmenu'
    

class PBrandAPIView(BaseProductAPIView):
    permission_classes = [IsAdminOrSuperUser]
    serializer_class = PBrandSerializer
    model = PBrand
    # cache_key = 'brands_cache'


class GenericUploadImageAPIView(APIView):
    """
    Endpoint genérico para subir imágenes a ImgBB.
    Devuelve la URL de la primera imagen subida.
    """
    # 1. Verificar si es role == 'admin' o user.id == 1
    permission_classes = [IsAdminOrSuperUser]
    
    # 1 - Sobreescribir metodos para aplicar distintos parsers/permissions segun la peticion http
    def get_parsers(self):
        """If the method is POST, it returns MultiPartParser to allow file uploads
        For (GET, DELETE), it uses the default parsers defined in the base class or DRF settings."""
        if self.request.method == 'POST':
            return [MultiPartParser()]    # Parser para recibir archivos
        return super().get_parsers()
    
    def post(self, request):
        
        # 1. Validación de imágenes
        if not request.FILES:
            return Response({"detail": "No se enviaron archivos."}, status=status.HTTP_400_BAD_REQUEST)

        images = request.FILES.getlist('images')
        if not images:
            return Response({"detail": "El campo 'images' está vacío."}, status=status.HTTP_400_BAD_REQUEST)
            
        # 2. Procesar solo la primera imagen (evita procesar múltiples innecesariamente)
        first_image = images[0]
        try:
            url = utils.get_url_from_imgbb(first_image)    # Validaciones de ImgBB
            return Response({"success": True, "image_url": url}, status=status.HTTP_201_CREATED)

        except ValueError as e:  # Errores conocidos (ej: formato no soportado)
            return Response({"success": False, "detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:  # Errores inesperados
            # logger.error(f"Error subiendo imagen: {str(e)}")  # Loggear el error
            return Response(
                {"success": False, "detail": "Error interno al procesar la imagen."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )