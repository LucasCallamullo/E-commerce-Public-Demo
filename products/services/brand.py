from typing import Iterable, Any
from products.filters import get_filtered_entity_by_id, get_filtered_entity_by_slug
from products.models.brand import Brand
from django.db.models import QuerySet

from products.cache_utils import (
    set_products_cache, get_products_cache, KEY_BRANDS_LIST
)

class BrandService:
    
    VALUES_BRAND_PUB = ('id', 'name', 'slug', 'image_url', 'is_default')
    
    @classmethod
    def get_dashboard_list(cls) -> list[dict[str, Any]]:
        """
        Retrieves the brand list for the administrative dashboard.
        
        Returns all non-default brands using the cached public list.
        """
        return cls._get_brands_list_cache()

    @classmethod
    def get_brands_list(cls, *, brand_ids: set[int] | None = None) -> list[dict[str, Any]]:
        """
        Retrieves brands optimized for views, leveraging cache.

        If brand_ids are provided, it filters the cached list in memory 
        to avoid redundant database hits.
        """
        # 1. Get the full list from cache (or DB if expired)
        all_brands = cls._get_brands_list_cache()
    
        # 2. Filter in memory if specific IDs are requested
        if brand_ids:
            return [b for b in all_brands if b['id'] in brand_ids]
            
        return all_brands
    
    @classmethod
    def _get_brands_list_cache(cls) -> list[dict[str, Any]]:
        """
        Handles the caching logic for the master brand list.
        
        Returns:
            list[dict]: The list of all non-default brands.
        """
        # Global list caching
        cached = get_products_cache(cache_key=KEY_BRANDS_LIST)
        if cached is not None:
            return cached
        # We always fetch non-default brands as the "master list"
        brands = list(cls._get_qs_base(
            values=cls.VALUES_BRAND_PUB, get_all=False
        ))
        set_products_cache(cache_key=KEY_BRANDS_LIST, value=brands)
        return brands
    
    @classmethod
    def _get_qs_base(cls, *, 
        values: Iterable[str],
        brand_ids: set[int] = None,
        get_all: bool = False
    ) -> QuerySet:
        """
        Constructs a base QuerySet for Brands with common filtering and sorting logic.

        Args:
            values (Iterable[str]): A list of field names to be returned via the 
                `.values()` method (e.g., ['id', 'name']).
            brand_ids (set[int], optional): A set of specific Brand IDs to filter the 
                results. If None, no ID filtering is applied. Defaults to None.
            get_all (bool, optional): If True, retrieves all brands including 
                system defaults. If False, filters out records where `is_default` 
                is True. Defaults to False.

        Returns:
            QuerySet: A deferred QuerySet containing dictionaries of the specified 
                fields, ordered alphabetically by name.

        Example:
            >>> fields = ('id', 'name')
            >>> brands = cls._get_qs_base(values=fields, brand_ids={1, 2, 3})
        """
        qs = Brand.objects.all()
        
        if not get_all:
            # Exclude system-protected or default placeholder brands
            qs = qs.filter(is_default=False)
            
        if brand_ids:
            qs = qs.filter(id__in=brand_ids)
        
        # Return specific fields to optimize memory and database payload
        return qs.values(*values).order_by('name')
    
    
    @staticmethod
    def get_filtered_by_id(*, entity_id: int | None = None) -> dict | None:
        """
        Retrieves a filtered product category by its identifier or returns
        the default category when requested.
        
        Parameters:
            entity_id (int | None):
                PBrand identifier. If None, no filtering is applied and None is returned.
                If 0, the default category (is_default=True) is returned.
                
        Returns:
            dict | None:
                Dictionary containing the category fields:
                - id
                - slug
                - name

                Returns None if no matching category is found.
        """
        values = ('id', 'slug', 'name', 'is_default')
        return get_filtered_entity_by_id(
            model=Brand,
            id_value=entity_id,
            values=values
        )
        
    
    @staticmethod
    def get_filtered_by_slug(*, entity_slug: str | None = None) -> dict | None:
        """
        Retrieves a filtered product category by its identifier or returns
        the default category when requested.
        """
        values = ('id', 'slug', 'name')
        return get_filtered_entity_by_slug(
            model=Brand,
            slug_value=entity_slug,
            values=values
        )
        
        
    