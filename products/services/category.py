from typing import Any
from django.core.cache import cache

from products.filters import get_filtered_entity_by_id, get_filtered_entity_by_slug
from products.models.category import Category
from products.models.subcategory import Subcategory

from products.cache_utils import (
    set_products_cache, get_products_cache, 
    KEY_CATEGORIES_LIST
)

class CategoryService:
    """
    Read-only service responsible for retrieving categories and subcategories
    optimized for public navigation elements (cards, filters, dropdowns).

    This service builds a minimal category → subcategory tree and optionally
    caches it to avoid repeated database queries.
    """
    
    VALUES_CATEGORY_PUB = ('id', 'name', 'slug')
    VALUES_SUBCATEGORY_PUB = ('id', 'name', 'slug', 'category_id')
    
    @staticmethod
    def get_dashboard_list() -> list[dict[str, Any]]:
        # Build minimal category tree and store it in cache
        categories_tree = (
            CategoryService
            ._build_categories_tree(
                values_category=('id', 'name', 'image_url'),
                values_subcategory=('id', 'name', 'category_id', 'image_url'),
                get_all=False
            )
        )
        return list(categories_tree.values())

    @classmethod
    def get_categories_list(cls) -> list[dict[str, Any]]:
        """
        Retrieve categories and their subcategories optimized for product card views.

        Returns:
            list[dict[str, Any]]:
            A list of category entries, each containing the category data and
            its associated subcategories.

        Example:
            [
                {
                    "category": {
                        "id": 1,
                        "name": "Electronics",
                        "slug": "electronics"
                    },
                    "subcategories": [
                        {
                            "id": 10,
                            "name": "Phones",
                            "slug": "phones",
                            "category_id": 1
                        },
                        ...
                    ] # or []
                },
                ...
            ]
        """
        cached = get_products_cache(KEY_CATEGORIES_LIST)
        if cached is not None:
            return list(cached.values())
        
        # Build minimal category tree and store it in cache
        categories_tree = cls._build_categories_tree(
            values_category = cls.VALUES_CATEGORY_PUB,
            values_subcategory = cls.VALUES_SUBCATEGORY_PUB
        )
        cls._set_cache_categories(categories_tree)
        return list(categories_tree.values())
    
    @classmethod
    def get_products_by_category(cls, products: list[dict], categories: list[dict]) -> list[dict]:
        """
        Groups a flat list of products into a structured format categorized by their parent category.

        This method transforms a flat product list into a hierarchical structure suitable for 
        rendering UI sections (e.g., category-based carousels or grids). It uses an internal 
        mapping to ensure high performance (O(n)) by avoiding nested loops for category lookups.

        Args:
            products (list[dict]): A list of product dictionaries. Each dictionary must 
                contain at least a 'category_id' key.
            categories (list[dict]): A list of category data dictionaries, typically 
                containing nested "category" objects with 'id', 'name', and 'slug'.

        Returns:
            list[dict]: A list of grouped category objects. Each object contains:
                - 'id': The category ID.
                - 'name': The category name.
                - 'slug': The category slug.
                - 'products': A list of all products belonging to that category.

        Example Output:
            [
                {
                    "id": 1, "name": "Electronics", "slug": "electronics",
                    "products": [{"id": 10, "name": "Smartphone", ...}, ...]
                },
                ...
            ]
        """
        # 1. Map category metadata by referencing the inner 'category' dict directly
        category_map: dict[int, dict] = {
            c["category"]["id"]: c["category"] 
            for c in categories
        }
        # 2. Group products into their respective categories
        products_by_category = {}
        for p in products:
            
            cat_id = p.get("category_id")
            cat_info = category_map.get(cat_id)
            
            if not cat_info:
                continue
            
            if cat_id not in products_by_category:
                # We use {**cat_info} to create a copy so we don't mutate 
                # the original category_map entry when adding the 'products' list
                products_by_category[cat_id] = {**cat_info, "products": []}
            
            products_by_category[cat_id]["products"].append(p)
        # 3. Return as a list of dictionaries for easier template iteration
        return list(products_by_category.values())
    
    
    @staticmethod
    def get_filtered_by_id(*, entity_id: int | None = None) -> dict | None:
        """
        Retrieves a filtered product category by its identifier or returns
        the default category when requested.
        
        Parameters:
            entity_id (int | None):
                Category identifier. If None, no filtering is applied and None is returned.
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
            model=Category,
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
            model=Category,
            slug_value=entity_slug,
            values=values
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _set_cache_categories(categories_tree: dict[int, dict[str, Any]]) -> None:
        """
        Store the built category tree in cache.

        Args:
            categories_tree (dict):
                Dictionary keyed by category ID containing category and
                subcategory data.
        """
        set_products_cache(cache_key=KEY_CATEGORIES_LIST, value=categories_tree)

    @staticmethod
    def _build_categories_tree(
        values_category: tuple,
        values_subcategory: tuple,
        get_all: bool = False
    ) -> dict[int, dict[str, Any]]:
        """
        Build a category → subcategory tree structure.

        This method performs two lightweight queries using `.values()` to retrieve
        only the necessary fields and then groups subcategories under their
        corresponding category.

        Returns:
            dict[int, dict[str, Any]]:
            A dictionary keyed by category ID.

        Example:
            {
                1: {
                    "category": {
                        "id": 1,
                        "name": "Electronics",
                        "slug": "electronics"
                    },
                    "subcategories": [
                        {
                            "id": 10,
                            "name": "Phones",
                            "slug": "phones",
                            "category_id": 1
                        }
                    ]
                }
            }
        """
        # obtener segun bandera, es más para construir por dashboard or public
        qs_sub = Subcategory.objects.all()
        qs_cat = Category.objects.all()
        if not get_all:
            qs_cat = qs_cat.filter(is_default=False)
            
        categories = (
            qs_cat
            .values(*values_category)
            .order_by('name')
        )
        
        subcategories = (
            qs_sub
            .values(*values_subcategory)
            .order_by('name')
        )

        # Group subcategories by category ID
        subcats_by_cat: dict[int, list[dict]] = {}
        for sub in subcategories:
            subcats_by_cat.setdefault(sub['category_id'], []).append(sub)

        # Build final category tree
        categories_tree: dict[int, dict[str, Any]] = {}
        for cat in categories:
            cat_id = cat['id']
            categories_tree[cat_id] = {
                'category': cat,
                'subcategories': subcats_by_cat.get(cat_id, []),
            }

        return categories_tree
