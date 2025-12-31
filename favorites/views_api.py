from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from favorites.services import FavoritesService
from products.models.product import Product
from core.utils.utils_basic import valid_id_or_None


class ToggleFavoriteProduct(APIView):
    """
    API endpoint to toggle a product as a favorite for the authenticated user.
    
    - If the product is not yet in the user's favorites, it will be added.
    - If the product is already a favorite, it will be removed.
    - Updates the cached set of favorite product IDs for the user.
    
    Permissions:
        The user must be authenticated to perform this action.
    """
    # reduce la cantidad de peticiones a 15/min
    throttle_scope = 'favorites'
    
    def post(self, request, product_id):
        """
        Handle POST requests to add or remove a product from the user's favorites.
        
        Args:
            request (Request): DRF request object containing the authenticated user.
            product_id (int): ID of the product to toggle.
        
        Returns:
            Response: JSON response with a success message and HTTP status code.
        """
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return Response({'detail': 'Please login.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Validate product_id
        product_id = valid_id_or_None(product_id)
        if not product_id:
            return Response({'detail': 'Product ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            added = FavoritesService.toggle_favorite(request.user, product_id)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        set_favs_ids = FavoritesService.get_favorite_ids(user=request.user)

        return Response(
            {
                'detail': 'Product added to favorites' if added else 'Product removed from favorites',
                'favorites_ids': list(set_favs_ids),
                'is_favorite': product_id in set_favs_ids
            }, 
            status=status.HTTP_200_OK
        )
        
