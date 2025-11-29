

from django.core.cache import cache
from products.filters import get_categories_n_subcategories

def get_categories_n_subcats(request):
    # Tries to get the data from the cache to optimize performance by querying only once
    # instead of doing it every time
    categories_dropmenu = cache.get('categories_dropmenu')
    
    if not categories_dropmenu:
        
        categories_dropmenu = get_categories_n_subcategories(from_cache=True)
        # Save the data in the cache for 1 hour (3600 seconds)
        cache.set('categories_dropmenu', categories_dropmenu, 3600)
    
    return {'categories_dropmenu': categories_dropmenu}