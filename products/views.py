

# Create your views here.
from django.shortcuts import render
from django.db.models import F

from products.models import Product, PCategory, PSubcategory, PBrand
from products.serializers import ProductListSerializer
from products import filters, utils

from favorites.utils import get_favs_products
from users.permissions import admin_or_superuser_required
import json


def product_list(request, cat_slug=None, subcat_slug=None, brand_slug=None):
    """Vista para listar productos con filtros opcionales."""
    
    def _get_filtered_entity(model, slug_value, is_default=False):
        """Función helper interna para obtener entidades filtradas por slug."""
        if not slug_value:
            return None
        return (
            model.objects.filter(slug=slug_value, is_default=is_default)
            .values('id', 'slug', 'name')
            .first()
        )

    # Obtener filtros usando la función helper interna
    category = _get_filtered_entity(PCategory, cat_slug, is_default=False)
    subcategory = _get_filtered_entity(PSubcategory, subcat_slug, is_default=False)
    brand = _get_filtered_entity(PBrand, brand_slug, is_default=False)
    
    # Normalizar búsqueda
    top_query = utils.normalize_or_None(request.GET.get('topQuery', ''))
    
    # Aplicar filtros
    filter_args = {
        'category': category.get('id') if category else None,
        'subcategory': subcategory.get('id') if subcategory else None,
        'brand': brand.get('id') if brand else None,
        'stock': True,
        'query': top_query,
    }
    products = filters.get_products_filters(filter_args)
    products = (
        products.values(*filters.VALUES_CARDS_LIST)
        .order_by('price', 'id').annotate(
            category_id=F("category__id"),
            subcategory_id=F("subcategory__id"),
            brand_id=F("brand__id"),
        )
    )
    # products = products.values(*filters.VALUES_CARDS_LIST).order_by('price', 'id')
    
    # Paginación
    page_num = request.GET.get('page')
    products_page, pagination = filters.get_paginator(
        products=products, 
        page_num=page_num, 
        quantity=100
    )
    
    # get unique brands on page for some utils select forms 
    # maybe in the future apply this for performance
    # brand_ids_in_page = {p['brand_id'] for p in products_page}
    brands = filters.get_serializer_brands(values=('id', 'name', 'slug', 'image_url'))
    
    # get categories from cache 
    categories = filters.get_categories_n_subcategories(from_cache=True)
    
    # Serialización
    favorites_ids = get_favs_products(request.user)
    serializer = ProductListSerializer(
        products_page, 
        many=True, 
        context={'favorites_ids': favorites_ids}
    )
    
    context = {
        'productos_json': json.dumps(serializer.data),
        'pagination': pagination,
        'category': category,
        'subcategory': subcategory,
        'brand': brand,
        'brands_json': json.dumps(brands),
        'categories': json.dumps(list(categories.values()))
    }
    
    return render(request, "products/products_list.html", context)


from django.shortcuts import redirect
def product_detail(request, product_id, slug):
    """
    Args:
        id (int): ID of the product to search and display its detail.
        slug (str): slug of the product to search and display its detail.
    """
    value_id = utils.valid_id_or_None(product_id)
    if not value_id:
        return redirect('Home')
    
    try:
        product = (
            Product.objects
            .select_related('category', 'subcategory', 'brand')
            .only(*filters.PRODUCT_FIELDS_DETAIL_VIEW)
            .get(id=product_id, slug=slug)
        )
    except Product.DoesNotExist:
        return redirect('Home')
    
    # We get all the necessary data from the product
    category = product.category
    subcategory = product.subcategory
    brand = product.brand
    images_urls = product.get_all_images_url()
    context = {
        'product': product,
        'images_urls': images_urls,
        'category': category if not category.is_default else None,
        'subcategory': subcategory if not subcategory.is_default else None,
        'brand': brand if not brand.is_default else None
    }
    return render(request, 'products/product_detail.html', context)








from django.db.models import F
@admin_or_superuser_required
def reset_stocks(request):
    """
    Reinicia los stocks sumando el stock reservado al stock general para los productos afectados.
    """
    # Actualizar en bloque usando F() para optimizar
    Product.objects.filter(stock_reserved__gt=0).update(
        stock=F('stock') + F('stock_reserved'),
        stock_reserved=0  # Opcional: reinicia el stock reservado si es necesario
    )

    # Mensaje de confirmación para el usuario (si es necesario)
    return render(request, 'home/home.html')
