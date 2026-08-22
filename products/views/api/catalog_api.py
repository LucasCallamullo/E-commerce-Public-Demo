from abc import abstractmethod
from typing import Callable
from django.core.cache import cache
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from django.conf import settings
from django.db.models import Value, F
from django.db.models.functions import Concat

# core app
from core.permissions import IsAdminOrSuperUser
from core.views.get_object_mixin import GetObjectMixin

# products app
from products.models.brand import Brand
from products.models.category import Category
from products.models.subcategory import Subcategory
from products.serializers.catalog_serializer import (
    BrandSerializer, CategorySerializer, SubcategorySerializer
)

# import logging
# logger = logging.getLogger(__name__)
class BaseCatalogAPIView(APIView, GetObjectMixin):
    """
    Abstract Base View for Catalog Entities (Category, Subcategory, Brand).
    
    Architecture Design:
    - Standardized CRUD lifecycle using DRF and custom Mixins.
    - Decoupled Side Effects: Physical file cleanup and cache invalidation
      are delegated to 'post_save' and 'post_delete' signals to ensure
      database transaction atomicity and system performance.
    - Protected Record Guard: Prevents modification of 'is_default' system records.
    - Optimized Reads: GET methods utilize .values() and DB-level annotations
      for high-performance data retrieval without model instance overhead.

    Attributes:
        model_class (Model): The Django model to query.
        serializer_class (Serializer): The DRF serializer for the specific model.
    """
    model_class = None
    serializer_class = None
    
    @abstractmethod
    def get_service_callback(self, pk: any) -> Callable:
        """
        MUST return a lambda or callable that returns a Model instance or None.
        """
        pass
    
    def post(self, request) -> Response:
        """
        Creates a new catalog entity.
        
        Note:
            - Data validation and unique constraints are handled by the Serializer.
            - Automatic cache invalidation and auxiliary side effects are 
              triggered via post_save signals after successful creation.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return self.success_response(
            key=self.model_name.lower(),
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )
        
    def patch(self, request, pk: int | str) -> Response:
        """
        Updates an existing catalog entity.
        
        Note:
            - System-protected records (is_default) cannot be modified.
            - Slug regeneration (if name changes) is handled by Model Mixins.
            - Physical file cleanup and cache invalidation are delegated to 
              post_save signals to ensure database consistency.
        """
        # Retrieve instance; raises NotFound if not found via Mixin logic
        instance = self.get_from_service_or_error(
            obj_id=pk,
            model_name=self.model_name,
            service_call=self.get_service_callback(pk)
        )
        # Check if the record is protected (system default)
        self._check_default_restriction(instance)
        
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return self.success_response(key=self.model_name.lower(), data=serializer.data)

    def delete(self, request, pk: int | str) -> Response:
        """
        Deletes the entity.
        
        Note:
            - Physical file cleanup and cache invalidation are delegated to 
              post_delete signals to ensure database consistency.
        """
        # Retrieve instance; raises NotFound if not found via Mixin logic
        instance = self.get_from_service_or_error(
            obj_id=pk,
            model_name=self.model_name,
            service_call=self.get_service_callback(pk)
        )
        # Check if the record is protected (system default)
        self._check_default_restriction(instance)
        
        # build response before delete
        deleted = { 'id': instance.id, 'name': instance.name }
        instance.delete()
        return self.success_response(
            key=self.model_name.lower(), data=deleted, 
            detail=f"{self.model_name} successfully deleted."
        )
    
    def get(self, request, pk: int | str = None) -> Response:
        if pk:
            payload = self.get_values_or_error(self.model_class, pk)
            return self.success_response(key=self.model_name.lower(), data=payload)
        
        # 1. Definimos la base de la URL
        base_url = getattr(settings, 'CDN_URL', '')

        # 2. Lógica de listado con Annotate
        queryset = (
            self.model_class.objects.all()
            .annotate(
                # Concatenamos la URL base con el path guardado en el CharField
                full_image_url=Concat(Value(base_url), F('image_url'))
            )
        )
        
        # 3. Convertimos a lista de diccionarios
        payload = list(queryset.values())
        
        return self.success_response(
            key=self.plural_name, data=payload, 
            count=len(payload)
        )
    
    # ------------------------ Private Helpers and properties
    @property
    def model_name(self) -> str:
        """
        Extracts the singular verbose name from the model's Meta.
        Example: "Category" or "Subcategory"
        """
        return self.model_class._meta.verbose_name

    @property
    def plural_name(self) -> str:
        """
        Extracts the plural verbose name from the model's Meta.
        Used for list response keys.
        """
        return self.model_class._meta.verbose_name_plural.lower().replace(" ", "_")
    
    def _check_default_restriction(self, instance):
        """
        Prevents modification of standard system records.
        Raises a PermissionDenied (403) if the instance is marked as default.
        """
        is_default = instance.__dict__.get('is_default', False)
        if is_default:
            raise PermissionDenied("Standard system records cannot be modified or deleted.")


# --- Concrete Implementations ---

class CategoryAPIView(BaseCatalogAPIView):
    permission_classes = [IsAdminOrSuperUser]
    serializer_class = CategorySerializer
    model_class = Category
    
    def get_service_callback(self, pk):
        return lambda v_id: (
            Category.objects
            .only('id', 'name', 'slug', 'is_default', 'image_url')
            .filter(id=v_id)
            .first()          
        )
    
class SubcategoryAPIView(BaseCatalogAPIView):
    permission_classes = [IsAdminOrSuperUser]
    serializer_class = SubcategorySerializer
    model_class = Subcategory
    
    def get_service_callback(self, pk):
        return lambda v_id: (
            Subcategory.objects
            .select_related('category')
            .only('id', 'name', 'slug', 'image_url', 'category_id', 'category__id', 'category__name')
            .filter(id=v_id)
            .first()          
        )
    
class BrandAPIView(BaseCatalogAPIView):
    permission_classes = [IsAdminOrSuperUser]
    serializer_class = BrandSerializer
    model_class = Brand

    def get_service_callback(self, pk):
        return lambda v_id: (
            Brand.objects
            .only('id', 'name', 'slug', 'is_default', 'image_url')
            .filter(id=v_id)
            .first()          
        )
