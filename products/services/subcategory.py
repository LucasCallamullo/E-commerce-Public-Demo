from typing import Any
# from django.core.cache import cache
from products.filters import get_filtered_entity_by_id, get_filtered_entity_by_slug
from products.models.subcategory import Subcategory

class SubcategoryService:
    """
    Read-only service for subcategories.
    """

    @staticmethod
    def for_category(category_id: int) -> list[dict[str, Any]]:
        return list(
            Subcategory.objects
            .filter(category_id=category_id, is_default=False)
            .values('id', 'name', 'slug')
            .order_by('name')
        )

    @staticmethod
    def get_filtered_by_id(*, entity_id: int | None = None) -> dict | None:
        """
        Retrieves a filtered product category by its identifier or returns
        the default category when requested.
        
        Parameters:
            entity_id (int | None):
                PSubcategory identifier. If None, no filtering is applied and None is returned.
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
            model=Subcategory,
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
            model=Subcategory,
            slug_value=entity_slug,
            values=values
        )