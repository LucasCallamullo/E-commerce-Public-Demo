from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from django.core.cache import cache

from core.permissions import IsAdminOrSuperUser
from core.utils.utils_basic import valid_id_or_None

from products.models.brand import Brand
from products.models.category import Category
from products.models.subcategory import Subcategory

from products.serializers.categories_serializer import (
    PBrandSerializer, PCategorySerializer, PSubcategorySerializer
)

class BaseProductAPIView(APIView):
    """
        Base APIView for simple CRUD operations on product-related models.
        Handles:
        - validation
        - default-object protection
        - cache invalidation
    """
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
        obj_id = valid_id_or_None(obj_id)
        if not obj_id:
            return None, Response(
                {"detail": "ID inválido"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        try: 
            instance = self.model.objects.get(id=obj_id)
        except self.model.DoesNotExist:
            return None, Response(
                {'detail': 'Model not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        if getattr(instance, 'is_default', False):    # si por algun motivo es el por defecto
            return None, Response(
                {"detail": "No se puede modificar un registro por defecto."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return instance, None
        
    def _invalidate_cache(self):
        if self.cache_key:
            cache.delete(self.cache_key)
            

class CategoryAPIView(BaseProductAPIView):
    permission_classes = [IsAdminOrSuperUser]
    serializer_class = PCategorySerializer
    model = Category
    cache_key = 'categories_dropmenu'
    

class SubcategoryAPIView(BaseProductAPIView):
    permission_classes = [IsAdminOrSuperUser]
    serializer_class = PSubcategorySerializer
    model = Subcategory
    cache_key = 'categories_dropmenu'
    

class BrandAPIView(BaseProductAPIView):
    permission_classes = [IsAdminOrSuperUser]
    serializer_class = PBrandSerializer
    model = Brand
    # cache_key = 'brands_cache'

