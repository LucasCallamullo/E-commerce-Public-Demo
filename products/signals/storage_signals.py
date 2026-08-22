# signals/storage_signals.py
from django.db import transaction
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from core.utils.utils_files import delete_physical_files_from_urls

import logging
logger = logging.getLogger(__name__)


@receiver(pre_save, sender='products.Brand')
@receiver(pre_save, sender='products.Category')
@receiver(pre_save, sender='products.Subcategory')
def catalog_cleanup_file_on_update(sender, instance, **kwargs):
    """
    Handles physical file deletion when an existing instance updates its image URL.
    """
    # from products.models.brand import Brand
    # from products.models.category import Category
    # from products.models.subcategory import Subcategory
    
    model_name = sender.__name__
    # 1. Skip if it's a new instance (no PK yet).
    if not instance.pk:
        now = instance.safe_original_url or 'NOT_LOADED'
        logger.info("[NEW_INSTANCE][%s] | New url: %s", model_name, now)
        return
    
    # 2. Skip if the URL hasn't changed (checked via needs_cleanup property).
    if not instance.needs_cleanup_file:
        # Access _original_url via getattr to avoid triggering deferred field loading.
        old = instance.safe_original_url or 'NOT_LOADED'
        url_for_log = instance.__dict__.get('image_url', '<DEFERRED>')
        
        logger.info("[NOT_NEW_URL][%s]: ID %s | New url: %s | Old url: %s", 
            model_name, instance.pk, url_for_log, old)
        return
    
    old_url = instance.safe_original_url
    
    # wrap the physical deletion in on_commit.
    # If the DB transaction fails and rolls back, the file remains safe on disk.
    # para que esto funcione en save, necesita un transaction.atomic encima
    transaction.on_commit(
        lambda url=old_url: delete_physical_files_from_urls(urls=[url])
    )
    
    logger.info("[SCHEDULED][%s]: image_url now: %s | on_commit for %s", 
        model_name, instance.image_url, old_url)
    # Update the internal state to prevent redundant triggers if save() is called 
    # again within the same execution context.
    instance.safe_original_url = instance.image_url
    
    logger.info("[STATE_SYNCED][%s]: Current url: %s | Private_attr: %s", 
        model_name, instance.image_url, instance.safe_original_url)


@receiver(post_delete, sender='products.Brand')
@receiver(post_delete, sender='products.Category')
@receiver(post_delete, sender='products.Subcategory')
def catalog_cleanup_file_on_delete(sender, instance, **kwargs):
    """
    Handles physical file deletion after an instance is removed from the database.
    The instance is still available in memory, allowing access to its attributes.
    """
    
    # Accessing __dict__ directly is the safest way to retrieve the value 
    # without triggering accidental 'Lazy Loading' queries, especially 
    # if the instance was deleted after a filtered query (like .only()).
    url = instance.safe_original_url
    if not url:
        return
    
    logger.info("[SCHEDULED DELETE][%s]: image_url: %s | Queuing file removal for %s", 
        sender.__name__, instance.image_url, url)
    
    # Ensure file is only deleted if the database transaction commits successfully.
    transaction.on_commit(
        lambda: delete_physical_files_from_urls(urls=[url])
    )
