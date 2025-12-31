from typing import Any
from django.core.cache import cache

from products.filters import get_filtered_entity_by_id, get_filtered_entity_by_slug
from products.models.category import Category
from products.models.subcategory import Subcategory

class CategoryService:
    """
    Read-only service responsible for retrieving categories and subcategories
    optimized for public navigation elements (cards, filters, dropdowns).

    This service builds a minimal category → subcategory tree and optionally
    caches it to avoid repeated database queries.
    """

    #: Cache key used to store the category tree
    CACHE_KEY = 'categories_dropmenu'

    #: Cache time-to-live in seconds (2 hours)
    CACHE_TTL = 60 * 120
    
    @staticmethod
    def for_dashboard() -> list[dict[str, Any]]:
        # Build minimal category tree and store it in cache
        categories_tree = (
            CategoryService
            ._build_categories_tree(
                values_category=('id', 'name', 'is_default', 'image_url'),
                values_subcategory=('id', 'name', 'is_default', 'category_id', 'image_url'),
                get_all=True
            )
        )
        return list(categories_tree.values())

    @staticmethod
    def for_cards(*, from_cache: bool = True) -> list[dict[str, Any]]:
        """
        Retrieve categories and their subcategories optimized for product card views.

        When `from_cache` is enabled, the category tree will be fetched from cache
        if available. Otherwise, the tree is rebuilt from the database and cached.

        Args:
            from_cache (bool): Whether to attempt retrieving data from cache first.

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
                        {
                            "id": 11,
                            "name": "Laptops",
                            "slug": "laptops",
                            "category_id": 1
                        }
                    ]
                },
                {
                    "category": {
                        "id": 2,
                        "name": "Furniture",
                        "slug": "furniture"
                    },
                    "subcategories": []
                }
            ]
        """
        if from_cache:
            cached = cache.get(CategoryService.CACHE_KEY)
            if cached:
                return list(cached.values())

        # Build minimal category tree and store it in cache
        categories_tree = CategoryService._build_categories_tree()
        CategoryService._set_cache_categories(categories_tree)

        return list(categories_tree.values())
    
    
    @staticmethod
    def get_categories_dropmenu(*, from_cache: bool = True) -> dict[int, dict[str, Any]]:
        if from_cache:
            cached = cache.get(CategoryService.CACHE_KEY)
            if cached:
                return cached

        # Build minimal category tree and store it in cache
        categories_tree = CategoryService._build_categories_tree()
        CategoryService._set_cache_categories(categories_tree)

        return categories_tree
        

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
        values = ('id', 'slug', 'name')
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
        cache.set(
            CategoryService.CACHE_KEY,
            categories_tree,
            timeout=CategoryService.CACHE_TTL,
        )

    @staticmethod
    def _build_categories_tree(
        values_category: tuple = ('id', 'name', 'slug'),
        values_subcategory: tuple = ('id', 'name', 'slug', 'category_id'),
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
        if not get_all:
            qs_cat = Category.objects.filter(is_default=False)
            qs_sub = Subcategory.objects.filter(is_default=False)
        else:
            qs_cat = Category.objects.all()
            qs_sub = Subcategory.objects.all()
            
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
