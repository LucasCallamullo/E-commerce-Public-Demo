from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.db import transaction

# home app
from home.cache_utils import delete_store_cache, KEY_STORE_PAYMENTS, KEY_STORE_PUBLIC

""" 
@receiver([post_save, post_delete], sender='home.Store')
@receiver([post_save, post_delete], sender='home.StoreImage')
@receiver([post_save, post_delete], sender='home.SocialMedia')
def clear_store_cache(sender, instance, **kwargs):
    # from home.models import Store, StoreImage, SocialMedia
    
    Invalidates the global store cache whenever store-related data is modified.
    
    Design Decision:
    We use a hardcoded store_id=1 because the current architecture supports 
    a single-store instance. This avoids unnecessary complexity in foreign 
    key lookups during cache invalidation.
    
    This ensures that changes to basic info, images, or social links are 
    immediately reflected on the public site by forcing the StoreService 
    to re-fetch and re-cache the 'Big Blob' on the next request.
    
    
    # maybe in the future apply this for generics but for now hardcoded store_id = 1
    # Identify the correct store_id based on the model triggered
    # if isinstance(instance, Store):
    #    store_id = instance.id
    # else:
        # For StoreImage and SocialMedia, we use the FK relation
    #    store_id = instance.store_id
    
    # Manejo de logs seguro para ambos signals
    def invalidate():
        # action = "DELETED" if kwargs.get('signal') == post_delete else "SAVED/UPDATED"
        # f"{action} SIGNAL {sender.__name__}"
        keys = [KEY_STORE_PUBLIC]
        
        # sender._meta.model_name devuelve el nombre de la clase en minúsculas
        if sender._meta.model_name == 'store':
            # solo en caso de editar la store invalidamos tambien esta key
            keys.append(KEY_STORE_PAYMENTS)
            
        delete_store_cache(store_id=1, contexts=keys)

    # Wait for the database to confirm the changes before clearing the cache.
    # This prevents the cache from being re-populated with stale data from an uncommitted transaction.
    transaction.on_commit(invalidate)
    
"""