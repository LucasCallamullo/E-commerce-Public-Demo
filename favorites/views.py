

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework.status import HTTP_401_UNAUTHORIZED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_200_OK

from products.models import Product
from favorites.models import FavoriteProduct
from favorites.utils import get_favs_products
from products.utils import valid_id_or_None
from django.core.cache import cache

class ToggleFavoriteProduct(APIView):
    
    def post(self, request, product_id):
        user = request.user
        if not user.is_authenticated:
            return Response({'detail': 'Please login session for save products.'}, status=HTTP_401_UNAUTHORIZED)

        product_id = valid_id_or_None(product_id)
        if not product_id:    # stupid check
            return Response({'detail': 'Product ID is required or not found'}, status=HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found.'}, status=HTTP_404_NOT_FOUND)

        favorite_product, created = FavoriteProduct.objects.get_or_create(user=user, product=product)
        
        # obtenemos el set cacheado o creado de nuevo
        favorites = get_favs_products(user, only_ids=True)
        if created:
            # este caso es nuevo favorito se agrega
            favorites.add(product_id)
        else:
            # este caso si ya existía significa que desfaveo, o sea se quita 
            favorites.discard(product_id)  # si es un set
        cache_key = f'user_favs_{user.id}'
        cache.set(cache_key, favorites, timeout=60*5)  # 5 min

        if not created:
            favorite_product.delete()
            return Response({'detail': 'Product removed from favorites'}, status=HTTP_200_OK)

        return Response({'detail': 'Product added to favorites'}, status=HTTP_200_OK)
