# home/cache_utils.py
from typing import Any, Callable, Iterable
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

# Base prefix for store-related cache entries to maintain a clean namespace
STORE_CACHE_PREFIX = 'store:global_data'
KEY_STORE_PAYMENTS = 'payments'
KEY_STORE_PUBLIC = 'public'

# Global Time-To-Live (TTL) for store cache in seconds (1 hour)
# This ensures data is refreshed periodically even if signals fail
CACHE_STORE_TTL = 60 * 60 * 24     # 24 Horas

"""
Expected JSON structure for 'store:global_data:<id>:payments':
{
    'id': int,
    'usd_exchange_rate': float/Decimal,
    'usd_last_update': datetime/str,
    'bank_name': str,
    'account_holder': str,
    'cuit': str,
    'cbu_cvu': str,
    'alias': str,
    'account_number': str
}


Expected JSON structure for 'store:global_data:<id>:public':
{
    'store': {
        'id': int,
        'name': str,
        'description': str,
        'address': str,
        'email': str,
        'cellphone': str,
        'wsp_number': str,
    },
    'social_networks': [
        {
            'platform': str,
            'url': str,
            'icon_class': str,  # e.g., 'ri-instagram-line'
        },
        ...
    ],
    'logo': {
        'image_url': str,
        'redirect_url': str,
    },
    'logo_wsp': {
        'image_url': str,
        'redirect_url': str,
    }
}
"""

def get_or_set_store_data(*, 
    store_id: int, 
    fetch_func: Callable[[], Any],
    key: str = KEY_STORE_PUBLIC
) -> dict[str, Any]:
    """
    Implements the Cache-Aside pattern (Lazy Loading) for store-related data.

    This utility attempts to retrieve data from the cache using a generated key. 
    If a cache miss occurs, it executes the provided callback function (fetch_func) 
    to retrieve fresh data, populates the cache for future requests, and returns the result.

    Args:
        store_id (int): The unique identifier of the store used to generate the cache key.
        fetch_func (Callable[[], Any]): A no-argument callback (usually a lambda or partial) 
                                        responsible for fetching data from the primary source 
                                        on a cache miss.

    Returns:
        dict[str, Any]: The cached or freshly fetched store data. Returns an empty dict 
                        or None if the fetch_func fails to retrieve data.
    """
    key = get_store_cache_key(store_id=store_id, key=key)
    data = cache.get(key)
    
    if data is None:
        data = fetch_func() 
        if data:
            cache.set(key, data, timeout=CACHE_STORE_TTL)
            logger.debug(f"[CACHE_MISS] Key {key} populated.")
    else:
        logger.debug(f"[CACHE_HIT] Key {key} retrieved.")
        
    return data


def get_store_cache_key(*, store_id: int, key: str = KEY_STORE_PUBLIC) -> str:
    """
    Generates a consistent cache key for a specific store instance and context.

    Args:
        store_id (int): The store's unique identifier.
        key (str): Context of the data ('public' or 'payments'). 
                        Use KEY_STORE_PUBLIC or KEY_STORE_PAYMENTS.

    Returns:
        str | None: Formatted key (e.g., 'store:global_data:1:public') or None if invalid.
    """
    if not store_id or key not in (KEY_STORE_PAYMENTS, KEY_STORE_PUBLIC):
        logger.warning(f"[CACHE] Invalid key parameters: id={store_id}, type={key}")
        return None
    
    return f"{STORE_CACHE_PREFIX}:{store_id}:{key}"


def delete_store_cache(store_id: int, contexts: Iterable[str]) -> None:
    """
    Invalidates specific cache contexts for a given store.

    Commonly used within signals to ensure that database updates are 
    immediately reflected by clearing the stale cache entries.

    Args:
        store_id (int): The unique identifier of the store.
        contexts (Iterable[str]): A collection of contexts to invalidate 
                                  (e.g., ['public', 'payments']).
    """
    for key in contexts:
        target_key = get_store_cache_key(store_id=store_id, key=key)
        
        if target_key:
            result = cache.delete(target_key)
            status = "CLEARED" if result else "MISS/EXPIRED"
            logger.debug(f"[CACHE_DELETE] Context: {key} | Key: {target_key} | Status: {status}")
