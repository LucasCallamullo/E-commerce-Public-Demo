

# Create your views here.
from django.shortcuts import render
from favorites.utils import get_favs_products

def cart_page_detail(request):
    
    user = request.user
    favorite_product_ids = []
    if user.is_authenticated:
        # IDs de productos favoritos
        favorite_product_ids = get_favs_products(user=user, only_ids=True)
    
    context = {
        # hay que convertir a lista porque los set, no son json serializable
        'favorite_product_ids': list(favorite_product_ids)
    }
    
    return render(request, "cart/cart_page_detail.html", context)
