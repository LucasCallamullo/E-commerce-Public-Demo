

from django.core.cache import cache

def get_favs_products(user, return_qs=False, only_ids=True, favorites_ids:set=None):
    from products.models import Product
    """
    Retrieves a user's favorite products in different formats depending on the parameters.

    Args:
        user (User): The authenticated user instance.
        return_qs (bool): If True, returns a Django QuerySet of Product objects.
        only_ids (bool): If True, returns only the set of favorite product IDs.

    Returns:
        set[int] | set[Product] | QuerySet[Product] | None:
            - Set of product IDs if only_ids is True (default).
            - QuerySet of Product objects if return_qs is True.
            - Set of full Product objects if both flags are False.
            - None if the user is not authenticated.
    """
    # Return None if the user is not logged in
    if not user.is_authenticated:
        return None
    
    cache_key = f'user_favs_{user.id}'
    fav_ids = cache.get(cache_key)

    # Return a set of product IDs (faster and lighter for comparisons)
    if fav_ids is None:
        fav_ids = set(user.favorites.values_list('product', flat=True))
        cache.set(cache_key, fav_ids, 300)  # cachea 5 minutos

    if only_ids and not return_qs:
        return fav_ids

    # Return a QuerySet of Product objects (allows further filtering and chaining)
    if return_qs:
        if favorites_ids:
            return Product.objects.filter(id__in=favorites_ids)
        return Product.objects.filter(id__in=user.favorites.values_list('product', flat=True))

    # Return a set of full Product objects using select_related to avoid extra DB hits
    user_favorites = user.favorites.select_related('product')
    return {fav.product for fav in user_favorites}
