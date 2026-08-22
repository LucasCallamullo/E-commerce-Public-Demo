# stores/services/store.py
from typing import Any, Iterable

from home.models.store import Store
from home.services.social_media import SocialMediaService
from home.services.store_image import StoreImageService
from home.cache_utils import get_or_set_store_data, KEY_STORE_PAYMENTS

class StoreService:
    """
    Service responsible for retrieving store-related data.

    Centralizes read-only access to Store information to keep
    ORM queries out of views and improve reusability.
    """
    PUBLIC_VALUES = (
        'id', 'name', 'description', 'schedules', 
        'address', 'email', 'cellphone', 'wsp_number'
    )
    
    FOR_PAYMENTS_VALUES = (
        'id', 'usd_exchange_rate', 'usd_last_update', 
        'bank_name', 'account_holder', 'cuit', 'cbu_cvu', 'alias', 'account_number',
    )
    
    # Combino ambos valores de arriba ya que son los mismos campos a editar
    DASHBOARD_VALUES = tuple(set(PUBLIC_VALUES + FOR_PAYMENTS_VALUES))
    
    # ---------- Public API ----------
    
    @classmethod
    def get_public_store(cls, *, store_id: int = 1) -> dict[str, Any] | None:
        """
        Shortcut to get only the basic store information from the public data.
        """
        data = cls.get_public_data(store_id=store_id)
        return data.get('store') if data else None
    
    @classmethod
    def get_usd_rate(cls, *, store_id: int = 1) -> str | None:
        """
        Calculates or retrieves the current USD exchange rate.
        Leverages the cached payment data to avoid redundant database hits.
        """
        data = cls.get_data_for_payments(store_id=store_id)
        return data.get('usd_exchange_rate') if data else None
    
    @classmethod
    def get_data_for_payments(cls, *, store_id: int = 1) -> dict[str, Any] | None:
        """
        Retrieves essential banking and exchange rate information for checkout processes.
        
        This method uses a cache-aside pattern to store payment instructions and 
        exchange rates, ensuring high performance during the critical checkout phase.
        """
        return get_or_set_store_data(
            store_id = store_id,
            key=KEY_STORE_PAYMENTS,
            fetch_func = lambda: cls._fetch_values(
                store_id=store_id,
                values=cls.FOR_PAYMENTS_VALUES
            )
        )
    
    @classmethod
    def get_public_data(cls, *, store_id: int = 1) -> dict[str, Any] | None:
        """
        Retrieves store-related data intended for the public website (footer, contact info, social links).
        
        This method acts as a high-level orchestrator that utilizes the cache-aside pattern 
        via 'get_or_set_store_data'. It ensures that expensive database lookups and 
        service aggregations are performed only when the cache is empty.

        Args:
            store_id (int): The unique identifier of the store. Defaults to 1.

        Returns:
            dict[str, Any] | None: A dictionary containing the 'Big Blob' of public 
                                   store data, or None if the store does not exist.
        """
        return get_or_set_store_data(
            store_id=store_id, 
            fetch_func=lambda: cls._fetch_full_store_data(store_id=store_id)
        )
    
    @classmethod
    def get_dashboard_details(cls, store_id: int = 1) -> dict[str, Any] | None:
        """
        Retrieves comprehensive store data for the administrative dashboard.

        This method includes sensitive fields (bank_name, cuit, etc.) and
        private configurations that are not intended for the public website.

        Returns:
            dict[str, Any] | None: A dictionary containing administrative fields, 
                                   or None if the record does not exist.
        """
        return cls._fetch_values(store_id=store_id, values=cls.DASHBOARD_VALUES)

    # ---------- Helpers  ----------
    
    @staticmethod
    def _fetch_values(*, store_id: int, values: Iterable[str],) -> dict[str, Any] | None:
        """
        Internal database fetcher to retrieve store fields as a dictionary.

        Uses an optimized .values() query to minimize memory overhead when 
        full model instances are not required.

        Args:
            values (Iterable[str]): The specific fields to include in the query.

        Returns:
            dict[str, Any] | None: The requested data as a dictionary, 
                or None if no match is found.
        """
        return Store.objects.filter(id=store_id).values(*values).first()

    @classmethod
    def _fetch_full_store_data(cls, *, store_id: int) -> dict[str, Any] | None:
        """
        Aggregates data from multiple services to build the complete public store dataset.

        This is an internal builder method (callback) triggered only on cache misses. 
        It consolidates basic store information, social media profiles, and branding assets
        (logos) into a single nested dictionary.

        Returns:
            dict[str, Any] | None: The assembled dataset ready for caching, 
                                   or None if the primary store record is missing.
        """
        store_dict = cls._fetch_values(store_id=store_id, values=cls.PUBLIC_VALUES)
        if not store_dict:
            return None
        
        # The 'Big Blob' structure ensures context processors receive 
        # all necessary data in a single, ready-to-use package.
        data = {
            'store': store_dict,
            'social_networks': SocialMediaService.get_cache_payload(store_id=store_id),
            'logo': StoreImageService.get_main_by_type(store_id=store_id, image_type='logo'),
            'logo_wsp': StoreImageService.get_main_by_type(store_id=store_id, image_type='logo_wsp'),
        }
        return data