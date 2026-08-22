from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.db import transaction

# products app
from products.cache_utils import delete_products_cache, get_products_cache_key

@receiver([post_save, post_delete], sender='products.Brand')
@receiver([post_save, post_delete], sender='products.Category')
@receiver([post_save, post_delete], sender='products.Subcategory')
def clear_catalog_cache(sender, instance, **kwargs):
    """
    Unified signal receiver to invalidate product-related cache.
    Works for Brand, Category, and Subcategory updates or deletions.
    """
    # from products.models.brand import Brand
    # from products.models.category import Category
    # from products.models.subcategory import Subcategory
    
    # Map the sender model name to our cache keys
    # 'sender.__name__' will be 'Brand', 'Category', or 'Subcategory'
    cache_key = get_products_cache_key(model_name=sender.__name__.lower())
    
    if not cache_key:
        return

    def invalidate():
        action = "DELETED SIGNAL" if kwargs.get('signal') == post_delete else "SAVED/UPDATED SIGNAL"
        delete_products_cache(cache_key=cache_key, action=action)
        
    # Wait for the database to confirm the changes before clearing the cache.
    # This prevents the cache from being re-populated with stale data from an uncommitted transaction.
    transaction.on_commit(invalidate)

