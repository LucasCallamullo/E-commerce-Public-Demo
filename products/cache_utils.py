# products/cache_utils.py
from typing import Any, Optional
from django.core.cache import cache

import logging
logger = logging.getLogger(__name__)

# --- Cache Keys Configuration ---
# Standardized keys for catalog entities to ensure namespace consistency.
KEY_CATEGORIES_LIST = 'categories_list'
KEY_BRANDS_LIST = 'brands_list'

# Global Time-To-Live (TTL) for cache entries in seconds (1 hour).
# Acts as a fallback mechanism if invalidation signals fail.
CACHE_GLOBAL_TTL = 60 * 60


#: Cache time-to-live in seconds (2 hours), is for temporal list on dashboard admin edits
CACHE_TEMP_TTL = 60 * 120

""" 
Example of key -> 'categories_list'
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


# Mapping model identifiers to their respective cache keys.
# Note: Both 'category' and 'subcategory' target the same key to 
# force a full menu refresh when either is modified.
CACHE_KEY_MAP = {
    'category': KEY_CATEGORIES_LIST,
    'subcategory': KEY_CATEGORIES_LIST,
    'categories': KEY_CATEGORIES_LIST,
    'brand': KEY_BRANDS_LIST,
    'brands': KEY_BRANDS_LIST,
}


def get_products_cache_key(*, model_name: Optional[str]) -> Optional[str]:
    """
    Retrieves the standardized cache key for a given model name.
    
    Args:
        model_name (str): The name of the entity (e.g., 'category').
        
    Returns:
        Optional[str]: The mapped cache key or None if not found.
    """
    if not model_name:
        return None
    
    return CACHE_KEY_MAP.get(model_name.lower())
    

def get_products_cache(cache_key: str | None) -> Optional[dict]:
    logger.debug("[CACHE_GET] Key '%s' get.", cache_key)
    return cache.get(cache_key)

    
def set_products_cache(cache_key: str | None = None, 
    model_name: str | None = None, value: Any | None = None) -> bool:
    """
    Persists data in the cache using the mapped key for the specified model.
    
    Args:
        cache_key (Optional[str]): The specific key to delete.
        model_name (Optional[str]): Entity identifier to determine the cache key.
        value (Any): Data to be stored (typically a list of dicts).
        
    Returns:
        bool: True if the operation was triggered.
    """
    target_key = cache_key or get_products_cache_key(model_name=model_name)
    
    if not target_key or not value:
        return False
    
    cache.set(target_key, value, timeout=CACHE_GLOBAL_TTL)
    logger.debug("[CACHE_SET] Key '%s' updated.", target_key)
    return True


def delete_products_cache(cache_key: str | None = None, 
    model_name: str | None = None, action: str = '') -> bool:
    """
    Invalidates a cache entry either by explicit key or by model mapping.
    
    Args:
        cache_key (Optional[str]): The specific key to delete.
        model_name (Optional[str]): The model whose associated key should be deleted.
        action (str): Solo para debug, no es necesario
        
    Returns:
        bool: True indicating the cleanup process was executed.
    """
    target_key = cache_key or get_products_cache_key(model_name=model_name)
    
    if target_key:
        result = cache.delete(target_key)
        status = "SUCCESS" if result else "NOT_FOUND/EXPIRED"
        logger.debug("[CACHE_DELETE] Key '%s' | status: %s | action: %s", target_key, status, action)
    
    return True
