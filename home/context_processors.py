

from django.core.cache import cache
from home.models import Store

def get_ecommerce_data(request):
    store = cache.get('store')
    
    if not store:
        store = Store.objects.filter(id=1).values(
            'id',
            'name',
            'logo',
            'logo_wsp',
            'ig_url',
            'tw_url',
            'fb_url',
            'tt_url',
            'google_url',
            'wsp_number',
            'address',
            'cellphone',
            'email'
        ).first()  # Usar first() para obtener solo un registro
        
        cache.set('store', store, 3600)

    return {'store': store}

    
    