
from typing import Set
from django.contrib.auth.models import User


class FavoritesClient:
    """
    Client for interacting with the favorites module.
    Centralizes all favorites-related operations and dependencies.
    Delegates actual data fetching to FavoritesService.
    """

    @staticmethod
    def get_qs_favs_products(user, favorites_ids: set = None):
        """
        Returns a QuerySet of favorite products for a user.

        Args:
            user (User): Django user instance.
            favorites_ids (set, optional): Pre-fetched favorite IDs to avoid extra queries.
        
        Returns:
            QuerySet[Product]: QuerySet of Product objects, empty if user has no favorites.
        """
        try:
            # Lazy import to avoid circular dependencies and optional dependency
            from favorites.services import FavoritesService
            # Use the centralized utility function with ID-only optimization
            return FavoritesService.get_favorites_qs(user, favorites_ids=favorites_ids)
        
        except ImportError as e:
            # Log module unavailability for debugging purposes
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Favorites module not available: {e}")
            return list()
        

    @staticmethod
    def get_user_favorites_ids(user: User) -> Set[int]:
        """
        Returns the set of favorite product IDs for a given user.

        Args:
            user (User): Django user instance.

        Returns:
            Set[int]: 
                -    Set of favorite product IDs, 
                -    empty Set if user has no favorites or not authenticated.
        """
        try:
            # Lazy import to avoid circular dependencies and optional dependency
            from favorites.services import FavoritesService
            # Use the centralized utility function with ID-only optimization
            return FavoritesService.get_favorite_ids(user)
        
        except ImportError as e:
            # Log module unavailability for debugging purposes
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Favorites module not available: {e}")
            
            # Graceful fallback: use direct ORM access if favorites relation exists
            if hasattr(user, 'favorites'):
                return set(user.favorites.values_list('product_id', flat=True))
            return set()
        
        
    @staticmethod
    def is_product_favorited(user: User, product_id: int) -> bool:
        """
        Checks if a specific product is in the user's favorites.

        Args:
            user (User): Django user instance.
            product_id (int): Product ID to check.

        Returns:
            bool: True if the product is favorited, False otherwise.
        """
        return product_id in FavoritesClient.get_user_favorites_ids(user)
