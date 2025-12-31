from typing import Iterable, Any
from products.filters import get_filtered_entity_by_id, get_filtered_entity_by_slug
from products.models.brand import Brand


class BrandService:
    """
    Read-only service for brand listings.
    """

    @staticmethod
    def _get_all_brands(values: Iterable[str]) -> list[dict[str, Any]]:
        """
        Retrieve all brands with selected fields.
        """
        return list(
            Brand.objects
            .values(*values)
            .order_by('name')
        )


    @staticmethod
    def _get_by_ids(
        *,
        brand_ids: set[int],
        values: Iterable[str],
    ) -> list[dict[str, Any]]:
        """
        Retrieve brands filtered by a set of IDs.
        """
        if not brand_ids:
            return []

        return list(
            Brand.objects
            .filter(id__in=brand_ids)
            .values(*values)
            .order_by('name')
        )

    @staticmethod
    def for_dashboard() -> list[dict[str, Any]]:
        values = ('id', 'name', 'is_default', 'image_url')
        return BrandService._get_all_brands(values)

    @staticmethod
    def for_cards(*, brand_ids: set[int] | None = None) -> list[dict[str, Any]]:
        """
        Brand list optimized for product card views.

        - If brand_ids is provided → filtered list
        - If brand_ids is None → all brands
        """
        values = ('id', 'name', 'slug', 'image_url')

        if not brand_ids:
            return BrandService._get_all_brands(values)

        return BrandService._get_by_ids(
            brand_ids=brand_ids,
            values=values
        )
        
    
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
        values = ('id', 'slug', 'name')
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
