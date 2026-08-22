from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

# core modules
from core.permissions import IsAdminOrSuperUser
from core.utils.utils_parsers import valid_id_or_None
from core.views.get_object_mixin import GetObjectMixin

# products
from products.serializers.product_serializer import ProductSerializer
from products.models.product import Product
from products.models.product_image import ProductImage
from products.filters import get_filters_from_request

# services products
from products.services.pagination import PaginationService
from products.services.product import ProductService
from products.services.brand import BrandService
from products.services.category import CategoryService
from products.services.subcategory import SubcategoryService


class ProductAPIView(APIView, GetObjectMixin):
    throttle_scope = 'search'
    
    def get_permissions(self):
        """Public access for GET, Admin only for write operations."""
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminOrSuperUser()]
    
    def post(self, request):
        """Creates a new product."""
        serializer = ProductSerializer(
            data=request.data, 
            context={
                'user': request.user, 
                'ip': request.META.get('REMOTE_ADDR')
            })
        
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return self.success_response(
            key="product", 
            data=serializer.data, 
            status_code=status.HTTP_201_CREATED
        )
        
    def patch(self, request, pk):
        """Partial update of a product with image context."""
        # Mixin handles validation and existence
        product = self.get_from_service_or_error(
            obj_id=pk,
            model_name='Product',
            service_call=lambda v_id: ProductService.get_product_for_update(entity_id=v_id)
        )
        
        # 3. Pasamos al serializer el objeto, la data/json(body), y actualizacion parcial de campos
        # Agregamos User y la IP Para Audit Service
        serializer = ProductSerializer(
            product, 
            data=request.data, 
            partial=True, 
            context={'user': request.user, 'ip': request.META.get('REMOTE_ADDR')}
        )
        
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return self.success_response(key="product", data=serializer.data)
    
    def get(self, request, pk=None):
        """
        Handles single product detail or filtered/paginated list.
        """
        if pk:
            # Optimized detail retrieval
            product = self.get_values_or_error(
                model_class=Product, 
                obj_id=pk, 
                values=(
                    'id', 'name', 'price', 'stock', 'description', 'main_image',
                    'category_id', 'category__name', 
                    'subcategory_id', 'subcategory__name', 
                    'brand_id', 'brand__name'
                )
            )
            return self.success_response(key="product", data=product)

        # List Logic
        filters = get_filters_from_request(request)    # get a dict of filters
        
        # Hydrate filter models (delegated to services)
        category = CategoryService.get_filtered_by_id(entity_id=filters.get('category'))
        subcategory = SubcategoryService.get_filtered_by_id(entity_id=filters.get('subcategory'))
        brand = BrandService.get_filtered_by_id(entity_id=filters.get('brand'))
        
        # Update IDs from hydrated models
        filters.update({
            'category': category.get('id') if category else None,
            'subcategory': subcategory.get('id') if subcategory else None,
            'brand': brand.get('id') if brand else None
        })
        
        # obtener queryset a partir de los filtros que vienen como request params
        qs = ProductService.qs_for_card_list(filters=filters)
        
        # Paginación ya devuelve una lista serializada con los products
        page_num = request.GET.get('page', 1)
        products, pagination = PaginationService.get_paginated_products(
            qs=qs, 
            page=page_num, 
            page_size=100, 
            user=request.user
        )
        
        return self.success_response(
            key="products", data=products,
            pagination=pagination,
            category=category,
            subcategory=subcategory,
            brand=brand,
            query=filters.get('query', ''),
            top_query=filters.get('top_query', ''),
            available=filters.get('available', False), 
            get_all=filters.get('get_all', False),
            filters=filters # Agrupamos los filtros para limpiar el root del JSON
        )
        """ 
        return Response({
            'products': products,
            'pagination': pagination,
            'category': category,
            'subcategory': subcategory,
            'brand': brand,
            'query': filters_args.get('query', ''),
            'top_query': filters_args.get('top_query', ''),
            'available': filters_args.get('available', False), 
            'get_all': filters_args.get('get_all', False)
        }, status=status.HTTP_200_OK)
        """