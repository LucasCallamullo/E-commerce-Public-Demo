# Create your views here.
from django.shortcuts import render
from core.clients.favorites_client import FavoritesClient


def cart_page_detail(request):
    """
    Renders the cart detail page for the current user.

    Retrieves the user's favorite product IDs and passes them to the template.

    Notes:
        - Favorite product IDs are retrieved via `FavoritesClient.get_user_favorites_ids`.
        - Converted to a list because sets are not JSON serializable and may be used in templates.
    """
    # Retrieve user's favorite product IDs
    favorite_product_ids = FavoritesClient.get_user_favorites_ids(user=request.user)
    
    return render(request, "cart/cart_page_detail.html", {
        # Convert set to list for JSON compatibility
        'favorite_product_ids': list(favorite_product_ids)  
    })