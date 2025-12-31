from django.shortcuts import render, redirect

# core module
from core.permissions import admin_or_superuser_required
from core.utils import utils_basic

# models
from products.models.product import Product

# services - products
from products.services.pagination import PaginationService
from products.services.products import ProductService
from products.services.brand import BrandService
from products.services.category import CategoryService
from products.services.subcategory import SubcategoryService


def product_list(request, cat_slug=None, subcat_slug=None, brand_slug=None):
    """Vista para listar productos con filtros opcionales."""
    
    # Obtener filtros usando la función helper interna
    category = CategoryService.get_filtered_by_slug(entity_slug=cat_slug)
    subcategory = SubcategoryService.get_filtered_by_slug(entity_slug=subcat_slug)
    brand = BrandService.get_filtered_by_slug(entity_slug=brand_slug)
    
    # Normalizar búsqueda
    top_query = utils_basic.normalize_or_None(request.GET.get('topQuery', ''))
    
    # Aplicar filtros
    filter_args = {
        'category': category.get('id') if category else None,
        'subcategory': subcategory.get('id') if subcategory else None,
        'brand': brand.get('id') if brand else None,
        'stock': True,
        'query': top_query,
    }
    # obtener queryset a partir de los filtros que vienen como request params
    qs = ProductService.qs_for_card_list(filters=filter_args)
    
    # Paginación ya devuelve una lista no ?
    page_num = request.GET.get('page', 1)
    products, pagination = PaginationService.get_paginated_products(
        qs=qs, 
        page=page_num, 
        page_size=100, 
        user=request.user
    )

    # get unique brands on page for some utils select forms 
    # maybe in the future apply this for performance
    # brand_ids_in_page = {p['brand_id'] for p in products_page}
    brands = BrandService.for_cards(brand_ids=None)
    
    # get categories from cache 
    categories = CategoryService.for_cards(from_cache=True)
    
    context = {
        'products': products,
        'pagination': pagination,
        'category': category,
        'subcategory': subcategory,
        'brand': brand,
        'brands': brands,
        'categories': categories
    }
    
    return render(request, "products/products_list.html", context)


def product_detail(request, product_id, slug):
    """
    Args:
        id (int): ID of the product to search and display its detail.
        slug (str): slug of the product to search and display its detail.
    """
    value_id = utils_basic.valid_id_or_None(product_id)
    if not value_id:
        return redirect('Home')
    
    try:
        product = ProductService.for_detail(entity_id=product_id, entity_slug=slug)
    except Product.DoesNotExist:
        return redirect('Home')
    
    # We get all the necessary data from the product
    category = product.subcategory.category
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
