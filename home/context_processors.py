
from home.services.store import StoreService

def get_ecommerce_data(request):
    """
    Injects global store configuration into the template context.
    
    This context processor retrieves the 'Big Blob' from StoreService, 
    which handles the caching logic. By nesting everything under 'store_info', 
    we avoid variable collisions in the global template scope.
    
    Expected JSON structure for 'store:global_data:<id>':
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
        'social_networks': 
            'all': [
                {
                    'platform': str,
                    'name': str,
                    'url': str,
                    'icon_class': str,  # e.g., 'ri-instagram-line'
                },
                ...
            ],
            'main': [
                {
                    'platform': str,
                    'name': str,
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
    # for stupid checks
    # from home.cache_utils import delete_store_cache
    # delete_store_cache(store_id=1)
    
    # Currently hardcoded to store_id=1 as it is a single-store platform.
    # Future multi-tenant support can replace this with request.store.id
    return {
        'store_info': StoreService.get_public_data(store_id=1)
    }
