from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

# core modules - otros
from core.permissions import IsAdminOrSuperUser
from core.utils.utils_basic import valid_id_or_None

# products
from products.serializers.product_serializer import ProductSerializer
from products.models.product import Product
from products.models.product_image import ProductImage
from products.filters import get_filters_from_request

# services products
from products.services.pagination import PaginationService
from products.services.products import ProductService
from products.services.brand import BrandService
from products.services.category import CategoryService
from products.services.subcategory import SubcategoryService


class ProductAPIView(APIView):
    throttle_scope = 'search'
    
    def get_permissions(self):
        """Permisos estrictos para POST y PATCH, para GET publico para otros"""
        if self.request.method in ('GET'):
            return [AllowAny()]
        
        # 1. Verificar si es role == 'admin' o user.id == 1
        return [IsAdminOrSuperUser()]    # Permissions custom en user.permissions
    
    
    def get(self, request, product_id=None):
        
        if product_id:
            pass
        
        else:
            filters_args = get_filters_from_request(request)
            
            # Obtener los modelos asociados en caso de estar presentes
            category = CategoryService.get_filtered_by_id(entity_id=filters_args.get('category'))
            subcategory = SubcategoryService.get_filtered_by_id(entity_id=filters_args.get('subcategory'))
            brand = BrandService.get_filtered_by_id(entity_id=filters_args.get('brand'))
            
            # obtener queryset a partir de los filtros que vienen como request params
            qs = ProductService.qs_for_card_list(filters=filters_args)
        
            # Paginación ya devuelve una lista serializada con los products
            page_num = request.GET.get('page', 1)
            products, pagination = PaginationService.get_paginated_products(
                qs=qs, 
                page=page_num, 
                page_size=100, 
                user=request.user
            )
            
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
    
    
    def post(self, request):
        serializer = ProductSerializer(data=request.data, context={'user': request.user})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        product = serializer.save()
        return Response({"success": True, "product_id": product.id}, status=status.HTTP_201_CREATED)
        
        
    def put(self, request, product_id):
        product_id = valid_id_or_None(product_id)
        if not product_id:
            return Response({"detail": "ID inválido: debe ser un número positivo"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Verificación de existencia (consulta a DB sólo si el ID es válido)
        try:
            product = ProductService.for_patch(entity_id=product_id)
        except Product.DoesNotExist:
            return Response({"success": False, "detail": "No existe el producto."}, status=status.HTTP_404_NOT_FOUND)
        
        # 3. llamar a servicio de product images
        images = ProductImage.objects.filter(product=product)
        
        # 4. Pasamos al serializer el objeto, la data/json(body), y actualizacion parcial de campos
        serializer = ProductSerializer(
            product, data=request.data, partial=True, 
            context={
                'user': request.user,
                'images': images,
                'ip': request.META.get('REMOTE_ADDR') # Agregamos la IP
            }
        )
        
        # 5. Verifica el formulario sino retorna algunos de los raise serializers.ValidationError
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        # 6. aca DRF llama internamente a update(instance, validated_data)
        serializer.save()
        return Response({"success": True, "product_id": product_id}, status=status.HTTP_200_OK)
    