# signals/storage_signals.py
from django.db import transaction
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

# core app
from core.utils.utils_files import delete_physical_files_from_urls

# necesario para que cachee antes
from home.models.store import Store

import logging
logger = logging.getLogger(__name__)

"""
@receiver(pre_save, sender='home.StoreImage')
def store_image_cleanup_file_on_update(sender, instance, **kwargs):
    # from home.models import StoreImage
    # type -> instance: StoreImage
    
    Handles physical file deletion when an existing instance updates its image URL.
    
    # 1. Skip if it's a new instance (no PK yet).
    if not instance.pk:
        now = instance.safe_original_url or 'NOT_LOADED'
        logger.info(f"[SKIP CLEANUP NEW INSTANCE]: ID {instance.pk} | New: {now}")
        return
    
    # 2. Skip if the URL hasn't changed (checked via needs_cleanup property).
    if not instance.needs_cleanup_file:
        # Access _original_url via getattr to avoid triggering deferred field loading.
        old = instance.safe_original_url or 'NOT_LOADED'
        url_for_log = instance.__dict__.get('image_url', '<DEFERRED>')
        logger.info(f"[SKIP CLEANUP_ NOT NEW URL]: ID {instance.pk} | New: {url_for_log} | Old: {old}")
        return
    
    old_url = instance.safe_original_url
    
    # wrap the physical deletion in on_commit.
    # If the DB transaction fails and rolls back, the file remains safe on disk.
    transaction.on_commit(
        lambda: delete_physical_files_from_urls(urls=[old_url])
    )
    
    logger.info(f"[SCHEDULED]: image_url now: {instance.image_url} | on_commit for {old_url}")
    # Update the internal state to prevent redundant triggers if save() is called 
    # again within the same execution context.
    instance.safe_original_url = instance.image_url
    
    logger.debug(f"[STATE SYNCED]: Current: {instance.image_url} | Private_attr: {instance.safe_original_url}")
"""
"""
@receiver(post_delete, sender='home.StoreImage')
def store_image_cleanup_file_on_delete(sender, instance, **kwargs):
    
    Handles physical file deletion after an instance is removed from the database.
    The instance is still available in memory, allowing access to its attributes.
    
    
    # Accessing __dict__ directly is the safest way to retrieve the value 
    # without triggering accidental 'Lazy Loading' queries, especially 
    # if the instance was deleted after a filtered query (like .only()).
    url = instance.safe_original_url
    if not url:
        logger.info(f"[CANCELED DELETE FILE]: instance.image_url: {url}")
        return
    
    url_for_log = instance.__dict__.get('image_url', '<DEFERRED>')
    logger.info(f"[SCHEDULED DELETE]: instance.image_url: {url_for_log} | Queuing file removal for {url}")
    
    # Ensure file is only deleted if the database transaction commits successfully.
    transaction.on_commit(
        lambda: delete_physical_files_from_urls(urls=[url])
    )
"""