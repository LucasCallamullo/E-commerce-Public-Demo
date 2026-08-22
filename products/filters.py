
from typing import Any
from core.utils.utils_parsers import valid_id_or_None


def get_filters_from_request(request) -> dict[str, Any]:
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
    # recuperar valores desde el request
    cat_id = valid_id_or_None(request.GET.get('category'), allow_zero=True) 
    subcat_id = valid_id_or_None(request.GET.get('subcategory'), allow_zero=True)
    brand_id = valid_id_or_None(request.GET.get('brand'), allow_zero=True)
    available = request.GET.get('available', '1')
    
    top_query = request.GET.get('topQuery', '')
    query = request.GET.get('query', '')
    
    # Aplicar filtros
    return {
        'category': cat_id,
        'subcategory': subcat_id,
        'brand': brand_id,
        'query': query.strip(),
        'top_query': top_query.strip(),
        'available': True if available == '1' else False, 
        'get_all': True if available == '2' else False,
    }
    

from typing import Type
from django.db.models import Model


def get_filtered_entity_by_id(
    *,
    model: Type[Model],
    id_value: int | None,
    values: tuple[str, ...] = ('id', 'slug', 'name'),
) -> dict | None:
    """
    Retrieves a filtered entity by its identifier or returns the default entity.

    Args:
        model (Model):
            Django model class (e.g. PCategory, PSubcategory, PBrand).

        id_value (int | None):
            Entity identifier. If None, returns None.
            If 0, returns the default entity (is_default=True).

        values (tuple[str]):
            Fields to be returned in the result dictionary.

    Returns:
        dict | None:
            Dictionary containing the requested fields, or None if not found.
    """
    if id_value is None:
        return None

    qs = model.objects.all()

    if id_value == 0 and ('is_default') in values:
        return qs.filter(is_default=True).values(*values).first()

    return qs.filter(id=id_value).values(*values).first()


def get_filtered_entity_by_slug(
    *,
    model: Type[Model],
    slug_value: str | None,
    values: tuple[str, ...] = ('id', 'slug', 'name'),
) -> dict | None:
    """
    Retrieves a filtered entity by its identifier or returns the default entity.

    Args:
        model (Model):
            Django model class (e.g. PCategory, PSubcategory, PBrand).

        slug_value (str | None):
            Entity slug identifier. If None, returns None.
            If "0", returns the default entity (is_default=True).

        values (tuple[str]):
            Fields to be returned in the result dictionary.

    Returns:
        dict | None:
            Dictionary containing the requested fields, or None if not found.
    """
    if slug_value is None:
        return None
    
    qs = model.objects.all()    # lazy
    
    # solo devuelve default en modelos con is_default, sino intnta buscar
    # y en caso de no existir devuelve None
    if slug_value == "0" and ('is_default') in values:
        return qs.filter(is_default=True).values(*values).first()    # lazy --> 

    return qs.filter(slug=slug_value).values(*values).first()
