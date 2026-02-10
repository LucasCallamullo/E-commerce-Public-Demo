from typing import Any
from home.models import SocialMedia


class SocialMediaService:
    """
    Service responsible for managing and retrieving social media business logic.

    This service centralizes all read operations for Social Media entities, 
    ensuring ORM queries are kept out of views and promoting data consistency 
    between the administration dashboard and the public-facing website.
    """
    # ---------- Public API ----------
    # Campos que sirven para el dashboard, y para operaciones PATCH, DELETE
    DASHBOARD_FIELDS = ('id', 'platform', 'url', 'is_main', 'is_active')
    CACHE_FIELDS = ('id', 'platform', 'url', 'is_main')

    @staticmethod
    def get_instance_by_id(*, store_id: int, network_id: int) -> SocialMedia | None:
        """
        Returns a model instance for write operations (update/delete).
        Uses .only() to load only the necessary fields into the object.
        """
        return (
            SocialMedia.objects
            .filter(id=network_id, store_id=store_id)
            .only(*SocialMediaService.DASHBOARD_FIELDS)
            .first()
        )

    @staticmethod
    def get_details_by_id(*, store_id: int, network_id: int) -> dict[str, Any] | None:
        """
        Returns a dictionary for read-only operations (API responses).
        This is faster and avoids extra DB hits.
        """
        net = (
            SocialMedia.objects
            .filter(id=network_id, store_id=store_id)
            .values(*SocialMediaService.DASHBOARD_FIELDS)
            .first()
        )
        if not net:
            return None
            
        return SocialMediaService._enrich_models(networks=[net])[0]

    @staticmethod
    def get_details_list(*, store_id: int) -> list[dict[str, Any]]:
        """
        Retrieves a complete list of social media records for a specific store.

        Returns:
            list[dict[str, Any]]: A list of enriched dictionaries containing 
                'id', 'platform', 'url', 'is_main', 'is_active', and UI helpers.
        """
        networks = list(
            SocialMedia.objects
            .filter(store_id=store_id)
            .values(*SocialMediaService.DASHBOARD_FIELDS)
            .order_by('-platform')
        )
        return SocialMediaService._enrich_models(networks=networks)
    
    @staticmethod
    def get_dashboard_list(*, store_id: int) -> list[dict[str, Any]]:
        """
        Retrieves the complete list of social networks for the management dashboard.

        Returns:
            list[dict[str, Any]]: A list of enriched dictionaries containing 
                'id', 'platform', 'url', 'is_main', 'is_active', and UI helpers.
        """
        networks = list(
            SocialMedia.objects
            .filter(store_id=store_id)
            .values(*SocialMediaService.DASHBOARD_FIELDS)
            .order_by('-platform')
        )
        return SocialMediaService._enrich_models(networks=networks)

    @staticmethod
    def get_cache_payload(*, store_id: int) -> dict[str, list[dict[str, Any]]]:
        """
        Assembles the social media data package optimized for public caching.

        This method filters for active networks, enriches them with icon classes 
        and labels, and organizes the result into a structured dictionary.
        The resulting payload is specifically designed to be persisted in Redis 
        and consumed by the 'context_processor' for public-facing components.

        Args:
            store_id (int): The unique identifier of the store.

        Returns:
            dict[str, list[dict[str, Any]]]: A dictionary with categorized lists:
                - 'all': All active networks.
                - 'main': Primary networks (limited to 4).
                - 'secondary': Non-primary networks (limited to 4).
        """
        networks = list(
            SocialMedia.objects
            .filter(store_id=store_id, is_active=True)
            .values(*SocialMediaService.CACHE_FIELDS)
            .order_by('-platform')
        )
        
        all_networks = SocialMediaService._enrich_models(networks=networks)
        
        return {
            'all': all_networks,
            'main': [n for n in all_networks if n['is_main']][:4],
            'secondary': [n for n in all_networks if not n['is_main']][:4]
        }

    # ---------- Helpers (Internal) ----------
    @staticmethod
    def _enrich_models(networks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Injects display-related metadata into raw database records.

        Args:
            networks (list[dict]): A list of dictionaries from a .values() query.

        Returns:
            list[dict[str, Any]]: The list of dictionaries with added 'icon_class' 
                and 'name' (human-readable label) keys.
        """
        if not networks:
            return []
        
        # Map platform keys (e.g., 'ig') to labels (e.g., 'Instagram') in memory
        platform_labels = dict(SocialMedia.PlatformEnum.choices)
        # We perform the mapping in memory to avoid extra DB joins
        return [
            {
                **network, 
                'icon_class': SocialMedia.get_icon_class(network['platform']),
                'name': platform_labels.get(network['platform'], 'Social Media')
            }
            for network in networks
        ]
