

from django.db import models
from django.db.models import Q, Prefetch, QuerySet
from typing import Dict, List, Optional, Literal, Union

from products.models import PCategory, PSubcategory, PBrand, ProductImage
from products.utils import valid_id_or_None

# CONST TUPLES FILTERS
# para desempaquetar la tupla como argumentos para .only().
PRODUCT_FIELDS_UPDATE = (
    'name', 'slug', 'normalized_name', 'price', 'price_list', 'available', 'stock',
    'description', 'discount', 'updated_at', 'main_image',
    'subcategory__id', 'subcategory__name',
    'category__id', 'category__name', 
    'brand__id', 'brand__name'
)






# this use in dashboard products section
VALUES_DASHBOARD_PRODUCTS = (
    'id', 'name', 'price', 'price_list', 'available', 'stock',
    'description', 'discount', 'updated_at', 'main_image',
    'subcategory__id', 'category__id', 'brand__id'
)


# this is use for a product_detail view
PRODUCT_FIELDS_DETAIL_VIEW = (
    'id', 'slug', 'name', 'price', 'price_list', 'available', 'stock',
    'description', 'discount', 'updated_at', 'main_image',
    'subcategory__slug', 'subcategory__name', 'subcategory__is_default',
    'category__slug', 'category__name', 'category__is_default',
    'brand__slug', 'brand__name', 'brand__is_default'
)

# this is use for a product_list.html / views.product_lsit
VALUES_CARDS_LIST = (
    'id', 'slug', 'name', 'price', 'price_list', 'available', 'stock',
    'discount', 'updated_at', 'main_image',
    'subcategory__id', 'category__id', 'brand__id'
    # 'subcategory__id', 'subcategory__slug', 'subcategory__name', 'subcategory__is_default',
    # 'category__id', 'category__slug', 'category__name', 'category__is_default',
    # 'brand__id', 'brand__slug', 'brand__name', 'brand__is_default'
)

def get_context_filtered_products(request) -> dict:
    """
    Extracts and validates filter parameters from the GET request, retrieves the filtered 
    list of products, and builds a context dictionary with relevant data for rendering.

    Parameters:
        request (HttpRequest): The incoming HTTP request containing GET parameters.

    Returns:
        dict: A context dictionary containing the following keys:
            - "products" (QuerySet): The filtered list of Product objects based on the parameters.
            - "category" (PCategory or None): The selected category object, or None if not found.
            - "subcategory" (PSubcategory or None): The selected subcategory object, or None if not found.
            - "brand" (PBrand or None): The selected brand object, or None if not found.
            - "available" (str): Availability filter value as a string ('0', '1', or '2'). Defaults to '1'.
                - '0' = only unavailable products
                - '1' = only available products
                - '2' = all products (available and unavailable)
            - "query" (str or None): The search query string, if any, used to filter products by name or other fields.
    """
    def _get_filtered_entity(model, id_value, is_default=False):
        """Función helper interna para obtener entidades filtradas por id."""
        if id_value is None:
            return None
        
        if id_value == 0:
            return (
                model.objects.filter(is_default=True)
                .values('id', 'slug', 'name')
                .first()
            )
        
        return (
            model.objects.filter(id=id_value, is_default=is_default)
            .values('id', 'slug', 'name')
            .first()
        )
    
    # recuperar valores desde el request
    cat_id = valid_id_or_None(request.GET.get('category'), allow_zero=True) 
    subcat_id = valid_id_or_None(request.GET.get('subcategory'), allow_zero=True)
    brand_id = valid_id_or_None(request.GET.get('brand'), allow_zero=True)
    available = request.GET.get('available', '1')
    query = request.GET.get('query', '')
    top_query = request.GET.get('topQuery', '')

    # Obtener filtros usando la función helper interna
    category = _get_filtered_entity(PCategory, cat_id, is_default=False)
    subcategory = _get_filtered_entity(PSubcategory, subcat_id, is_default=False)
    brand = _get_filtered_entity(PBrand, brand_id, is_default=False)
    
    # Aplicar filtros
    filter_args = {
        'category': category.get('id') if category else None,
        'subcategory': subcategory.get('id') if subcategory else None,
        'brand': brand.get('id') if brand else None,
        'query': query,
        'top_query': top_query,
        'available': True if available == '1' else False, 
        'get_all': True if available == '2' else False,
    }
    products = get_products_filters(filter_args)

    # retornar el contexto a utilizar en un template
    return {
        "products": products,
        "category": category,
        "subcategory": subcategory,
        "brand": brand,
        "available": available,
        "query": query,
    }


def get_products_filters(filters: dict) -> QuerySet:
    from products.models import Product
    """
    Filters products based on provided dictionary filters.
    
    Args:
        filters (dict): Dictionary with optional keys:
            - 'category' (id or None PCategory)
            - 'subcategory' (id or None PSubcategory)
            - 'brand' (id or None PBrand)
            - 'stock' (bool) -> True to -> stock__gt=0
            - 'query' (str)
            - 'top_query' (str)
            - 'available' (bool)
            - 'get_all' (bool): If True, returns all products regardless of 'available'.
        
    Returns:
        QuerySet[Product]: Filtered queryset (may be empty if no matches).
    """
    get_all = filters.get('get_all', False)      # if u want different value
    available = filters.get('available', True)   # if u want different value
    category = valid_id_or_None(filters.get('category'))            # ID || None
    subcategory = valid_id_or_None(filters.get('subcategory'))      # ID || None
    brand = valid_id_or_None(filters.get('brand'))      # ID || None
    query = filters.get('query', '')               
    top_query = filters.get('top_query', '')            # query STR || ''
    stock = filters.get('stock', False)  

    # Si all está activo, no se filtra por disponibilidad
    products = Product.objects.all() if get_all else Product.objects.filter(available=available)
    
    if stock:
        products = products.filter(stock__gt=0)

    if category:
        products = products.filter(category_id=category)

    if subcategory:
        products = products.filter(subcategory_id=subcategory)
        
    if brand:
        products = products.filter(brand_id=brand)

    if query or top_query:
        chain = f'{query} {top_query}'

        # 1. Creamos una lista de condiciones Q (consultas) para cada palabra en la búsqueda:
        #    - Cada Q busca coincidencias parciales (icontains) en el campo normalized_name
        #    - Ejemplo: si query = "zapatilla nike", crea [Q(normalized_name__icontains='zapatilla'), Q(...='nike')]
        queries = [Q(normalized_name__icontains=word) for word in chain.split()]

        # 2. Extraemos la última condición Q como base para combinar las demás:
        #    - Usamos pop() para evitar modificar la lista mientras iteramos
        query_filter = queries.pop()

        # 3. Combinamos todas las condiciones Q usando AND lógico (&):
        #    - Esto obliga a que todas las palabras de búsqueda estén presentes en el nombre normalizado
        #    - Ejemplo: query_filter = (Q por 'zapatilla') & (Q por 'nike')
        for q in queries:
            query_filter &= q
            # query_filter |= q    # OR LOGICO capaz alguna vez me sirve...

        # 4. Aplicamos el filtro combinado al queryset de productos:
        #    - La consulta SQL resultante tendrá una cláusula WHERE con múltiples LIKE unidos por AND
        #    - Ejemplo: WHERE normalized_name LIKE '%zapatilla%' AND normalized_name LIKE '%nike%'
        products = products.filter(query_filter)

    return products


from django.core.cache import cache
def get_categories_n_subcategories(
    from_cache=True, 
    from_dashboard=False,
    values_cat: tuple = ('id', 'name', 'slug'),
    values_sub: tuple = ('id', 'name', 'slug', 'category_id')
) -> Dict[int, Dict[str, Union[Dict, Optional[List[Dict]]]]]:
    """
    Retrieves a dictionary mapping each non-default product category to its corresponding list of subcategories.

    Parameters:
        from_cache (bool, optional): If True, attempts to retrieve the result from cache. 
            Defaults to True.
        values_cat (tuple, optional): Fields of the category model to include in the output. 
            Defaults to ('id', 'name', 'slug').
        values_sub (tuple, optional): Fields of the subcategory model to include in the output. 
            Defaults to ('id', 'name', 'slug', 'category_id').

    Returns:
        dict: A dictionary where:
            - Each key is a category ID (int).
            - Each value is a dictionary with:
                - 'category': a dict representing the category (with selected fields).
                - 'subcategories': a list of subcategory dicts (or None if no subcategories).

    Example:
        {
            1: {
                'category': {'id': 1, 'name': 'Electronics', 'slug': 'electronics'},
                'subcategories': [
                    {'id': 10, 'name': 'Phones', 'slug': 'phones', 'category_id': 1},
                    {'id': 11, 'name': 'Laptops', 'slug': 'laptops', 'category_id': 1}
                ]
            },
            2: {
                'category': {'id': 2, 'name': 'Furniture', 'slug': 'furniture'},
                'subcategories': None
            }
        }
        
    Use Template:
        {% for item in categories_dropmenu.values %}
            {{ item.category.id }}
            {% if item.subcategories %}
                {% for subcat in item.subcategories %}
                    {{ item.category.name }} - {{ subcat.slug }}
    """
    if from_cache and not from_dashboard:
        categories_dropmenu = cache.get('categories_dropmenu')
        
        # if categories_dropmenu and from_dashboard:
        #    categories_list = list(categories_dropmenu.values())
        #    return categories_list
        if categories_dropmenu:
            return categories_dropmenu
        
    # initial lazy queries to database depend on from_dashboard bool
    subcategories = (
        PSubcategory.objects.all() if from_dashboard 
        else PSubcategory.objects.filter(is_default=False)
    )
    categories = (
        PCategory.objects.all() if from_dashboard 
        else PCategory.objects.filter(is_default=False)
    )
    
    subcategories = subcategories.order_by('name').values(*values_sub) 
    categories = categories.order_by('name').values(*values_cat)
    
    # Create a dictionary mapping each category to its subcategories (if any) 
    subcats_by_cat = {}
    for sub in subcategories:
        cat_id = sub['category_id']
        if cat_id not in subcats_by_cat:
            subcats_by_cat[cat_id] = []
        subcats_by_cat[cat_id].append(sub)

    # Construir el diccionario final
    categories_dropmenu = {}
    for cat in categories:
        cat_id = cat['id']
        categories_dropmenu[cat_id] = {
            'category': cat,
            'subcategories': subcats_by_cat.get(cat_id) or []
        }
        
    # this need it to return in this format to dashboard panel
    if categories_dropmenu and from_dashboard:
        categories_list = list(categories_dropmenu.values())
        return categories_list

    return categories_dropmenu


from products.serializers import BrandListSerializer
def get_serializer_brands(
    brands_ids=None,
    values: tuple = ('id', 'name', 'slug', 'image_url'), 
    exclude_default: bool = True
) -> list[dict]:
    """
    Retrieve serialized brand data from the database with optional field selection 
    and the ability to exclude default brands.

    This function can optionally filter brands by a list of IDs, select specific 
    fields to include in the output, and exclude brands marked as default (is_default=True).

    Args:
        brands_ids (list[int], optional):
            List of brand IDs to include. If None, includes all brands.
        
        values (tuple, optional):
            A tuple of field names to include in the output dictionaries.
            Defaults to ('id', 'name', 'slug', 'image_url').

        exclude_default (bool, optional):
            Whether to exclude brands marked as default (is_default=True).
            Defaults to True.

    Returns:
        list[dict]:
            A list of dictionaries representing the serialized brand objects, 
            each containing only the requested fields.
    
    Example:
        >>> get_serializer_brands(brands_ids=[1, 2, 3], exclude_default=True)
        [
            {'id': 1, 'name': 'Brand A', 'slug': 'brand-a', 'image_url': 'http://...'},
            {'id': 2, 'name': 'Brand B', 'slug': 'brand-b', 'image_url': 'http://...'},
            ...
        ]
    """
    brands = PBrand.objects.all()
    
    if exclude_default:
        brands = brands.filter(is_default=False)
        
    if brands_ids:
        brands = brands.filter(id__in=brands_ids)
    
    brands = brands.values(*values).order_by('name')
    serializer = BrandListSerializer(brands, many=True)
    return serializer.data



from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
def get_paginator(products: QuerySet, page_num: int = 1, quantity: int = 100) -> tuple:
    """
    Paginates a Django QuerySet and returns the items for the current page
    along with pagination metadata.

    Args:
        products (QuerySet): Django QuerySet to be paginated.
        page_num (int): Current page number (defaults to 1).
        quantity (int): Number of items per page (defaults to 48).

    Returns:
        tuple: A tuple containing:
            - products_page (QuerySet): A sliced QuerySet containing items for the current page.
              If no items exist, returns the full original QuerySet or an empty list.
            - pagination (dict): A dictionary with pagination metadata:
                - 'page' (int): Current page number, or 0 if no valid page exists.
                - 'total_pages' (int): Total number of pages available.
    """
    paginator = Paginator(products, quantity)
    
    if page_num is None:
        page_num = 1

    try:
        # 3. Obtener la página actual
        page_obj = paginator.page(page_num)
    except PageNotAnInteger:
        # Si 'page' no es un entero, mostrar la primera página
        page_obj = paginator.page(1)
    except EmptyPage:
        # Si la página está fuera de rango (ej: 9999), mostrar la última página
        # page_obj = paginator.page(paginator.num_pages)
        if paginator.num_pages == 0:
            # No hay ningún resultado, devolver None o lista vacía segura
            page_obj = None
        else:
            # Página fuera de rango, mostrar la primera
            page_obj = paginator.page(1)
    
    
    products_page = page_obj.object_list if page_obj else products
    pagination = {
        'page': page_obj.number if page_obj else 0,
        'total_pages': page_obj.paginator.num_pages if page_obj else 0,
        'results_on_page': len(products_page),
        'total_results': paginator.count
    }
    return products_page, pagination