# favorites/services.py
from products.models.product import Product
from favorites.models import FavoriteProduct
from django.core.cache import cache


class FavoritesService:
    """
    Service to handle all business logic related to a user's favorite products.

    Provides methods to retrieve favorite products in different formats:
    - Set of product IDs
    - QuerySet of Product objects
    - Set of full Product objects
    """

    @staticmethod
    def get_favorite_ids(user) -> set[int]:
        """
        Retrieve the set of favorite product IDs for a given user, using caching.

        Args:
            user (User): The Django user instance. Can be anonymous.

        Returns:
            set[int]: A set of product IDs. Returns an empty set if the user is
                      not authenticated or has no favorites.
        """
        if not user.is_authenticated:
            return set()

        cache_key = FavoritesService._get_cache_key(user=user)
        fav_ids = cache.get(cache_key)
        
        # Return a set of product IDs (faster and lighter for comparisons)
        if fav_ids is None:
            fav_ids = set(user.favorites.values_list('product', flat=True))
            # guardar nuevo set como cache en caso de no haber antes
            FavoritesService._save_cache(favorites_ids=fav_ids, user=user)
            
        return fav_ids

    @staticmethod
    def get_favorites_qs(user, favorites_ids: set = None):
        """
        Retrieve the user's favorite products as a Django QuerySet.

        Args:
            user (User): The Django user instance. Can be anonymous.
            favorites_ids (set, optional): Pre-fetched set of favorite IDs. If
                                           None, the method fetches them.

        Returns:
            QuerySet[Product]: QuerySet of Product objects. Returns an empty
                               QuerySet if the user is not authenticated or
                               has no favorites.
        """
        
        if not user.is_authenticated:
            return Product.objects.none()

        if favorites_ids is None:
            favorites_ids = FavoritesService.get_favorite_ids(user)

        return Product.objects.filter(id__in=favorites_ids)

    @staticmethod
    def get_favorites_set(user):
        """
        Retrieve the user's favorite products as a Python set of Product objects.

        Args:
            user (User): The Django user instance. Can be anonymous.

        Returns:
            set[Product]: Set of Product objects. Returns an empty set if the user
                          is not authenticated or has no favorites.
        """
        if not user.is_authenticated:
            return set()

        user_favorites = user.favorites.select_related('product')
        return {fav.product for fav in user_favorites}

    @staticmethod
    def toggle_favorite(user, product_id: int) -> bool:
        """
        Toggle a product as a favorite for a user.

        Args:
            user (User): Django user instance.
            product_id (int): Product ID to toggle.

        Returns:
            bool: True if the product was added to favorites, False if removed.

        Raises:
            Product.DoesNotExist: If the product with the given ID does not exist.
        """
        # Try to fetch product, will raise Product.DoesNotExist if not found
        product = Product.objects.get(id=product_id)

        fav, created = FavoriteProduct.objects.get_or_create(user=user, product=product)

        # Update cached favorites
        favorites = FavoritesService.get_favorite_ids(user)
        
        if created:
            favorites.add(product_id)
        else:
            favorites.discard(product_id)
            fav.delete()

        FavoritesService._save_cache(favorites_ids=favorites, user=user)
        return created


    # ------------------------ Private methos for cache
    @staticmethod
    def _get_cache_key(user) -> str:
        """ Para centralizar la cache key en caso de querer cambiar a futuro """
        return f'user_favs_{user.id}'
    
    @staticmethod
    def _save_cache(favorites_ids: set, user) -> None:
        """ Para centralizar el guardado de cache productos favoritos """
        cache_key = FavoritesService._get_cache_key(user=user)
        cache.set(cache_key, favorites_ids, 600)  # cache 10 minutes
        