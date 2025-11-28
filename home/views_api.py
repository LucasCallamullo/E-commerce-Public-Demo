

from rest_framework.views import APIView
from rest_framework.response import Response  
from rest_framework import status  

from users.permissions import IsAdminOrSuperUser
from home.models import Store, StoreImage
from home.serializers import StoreSerializer, StoreImageSerializer
from products import utils

class StoreAPI(APIView):
    # 1. Verificar si es role == 'admin' o user.id == 1
    permission_classes = [IsAdminOrSuperUser]
    
    def patch(self, request, store_id):
        store_id = utils.valid_id_or_None(store_id)
        if not store_id:
            return Response({'detail': 'Invalid store ID'}, status=status.HTTP_400_BAD_REQUEST)
        
        # first() devuelve None si no encuentra ningún registro
        store = Store.objects.filter(id=store_id).first()
        if not store:
            return Response({'detail': 'Store not found'}, status=status.HTTP_404_NOT_FOUND)

        # Crea una instancia del serializador para actualizar el Store:
        # 1er argumento: instancia del modelo a actualizar (store)
        # data: datos recibidos en la petición (request.data)
        # partial=True: permite actualización parcial (no todos los campos son requeridos)
        serializer = StoreSerializer(store, data=request.data, partial=True)
        
        # Verifica si los datos pasan las validaciones del serializador
        if serializer.is_valid():
            # Si son válidos, guarda los cambios en la base de datos
            serializer.save()
            # Devuelve los datos actualizados en la respuesta
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        # Si los datos no son válidos, devuelve los errores de validación
        # con código de estado HTTP 400 (Bad Request)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class StoreImageAPI(APIView):
    permission_classes = [IsAdminOrSuperUser]
    
    def post(self, request, store_id, image_type):
        store, error = self._get_store(store_id=1)
        if error:
            return error
        
        image_type, error = self._resolve_image_type(image_type=image_type)
        if error:
            return error
        
        images = self._get_headers_for_context(store, image_type)
        
        serializer = serializer = StoreImageSerializer(data=request.data, partial=True, context={
            'store': store,
            'image_type': image_type,
            'images': images
        })
        
        if serializer.is_valid():
            image = serializer.save()
            return Response({"success": True, "image_id": image.id}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, store_id, image_type, image_id):
        store, error = self._get_store(store_id=1)
        if error:
            return error
        
        image_type, error = self._resolve_image_type(image_type=image_type)
        if error:
            return error
        
        image, error = self._get_image(image_id=image_id, image_type=image_type, store=store)
        if error:
            return error
        
        was_main = image.main_image
        image.delete()
        if was_main:
            self._set_next_main_image(store, image_type, exclude_id=image_id)

        # HTTP_204_NO_CONTENT
        return Response({"success": True, "detail": "image deleted"}, status=status.HTTP_200_OK)
            
    def patch(self, request, store_id, image_type, image_id):
        store, error = self._get_store(store_id=1)
        if error:
            return error
        
        image_type, error = self._resolve_image_type(image_type=image_type)
        if error:
            return error
        
        image, error = self._get_image(image_id=image_id, image_type=image_type, store=store)
        if error:
            return error
        images = self._get_headers_for_context(store, image_type, exclude_id=image_id)
        
        serializer = StoreImageSerializer(image, data=request.data, partial=True, context={
            'store': store,
            'images': images
        })
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        # Si los datos no son válidos, devuelve los errores de validación
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_image(self, image_id, image_type, store):
        image_id = utils.valid_id_or_None(image_id)
        if not image_id:
            return None, Response({'detail': 'Invalid Header Image ID'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            image = StoreImage.objects.get(id=image_id, image_type=image_type, store=store)
            return image, None
        except StoreImage.DoesNotExist:
            return None, Response({'detail': 'Header Image not found'}, status=status.HTTP_404_NOT_FOUND)
        
    def _get_store(self, store_id=1):
        # store_id = 1    # future: get from request or URL
        store_id = utils.valid_id_or_None(store_id)
        if not store_id:
            return None, Response({'detail': 'Invalid Store ID'}, status=status.HTTP_400_BAD_REQUEST)
        try: 
            store = Store.objects.only('id').get(id=store_id)
            return store, None
        except Store.DoesNotExist:
            return None, Response({'detail': 'Store not found'}, status=status.HTTP_404_NOT_FOUND)
        

    def _get_headers_for_context(self, store, image_type, exclude_id=None, available=True):
        queryset = StoreImage.objects.filter(store=store, available=available, image_type=image_type)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset
    
    def _set_next_main_image(self, store, image_type, exclude_id):
        next_main = self._get_headers_for_context(store, image_type, exclude_id=exclude_id).first()
        if not next_main:
            next_main = self._get_headers_for_context(store, image_type, exclude_id=exclude_id, available=False).first()
        if next_main:
            next_main.main_image = True
            next_main.save(update_fields=['main_image'])

    def _resolve_image_type(self, image_type: str):
        VALID_IMAGE_TYPES = ('header', 'banner', 'logo')
        image_type = image_type.lower().strip()
        if image_type not in VALID_IMAGE_TYPES:
            return None, Response({'detail': f"Invalid image type: '{image_type}'"}, status=status.HTTP_400_BAD_REQUEST)
        return image_type, None
