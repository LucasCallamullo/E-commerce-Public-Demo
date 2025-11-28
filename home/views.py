from django.shortcuts import render

# Create your views here.
from home.models import Store, StoreImage
from django.db.models import Prefetch, F


import json
from products.models import Product
from products.filters import VALUES_CARDS_LIST, get_serializer_brands, get_categories_n_subcategories
from products.serializers import ProductListSerializer

from favorites.utils import get_favs_products

def home(request):
    
    # Obtener el store con prefetch optimizado
    store = Store.objects.prefetch_related(
        Prefetch(
            'images', 
            queryset=StoreImage.objects.filter(available=True)
            .order_by('-main_image'),
            to_attr='all_images'
        ),
    ).get(id=1)
    
    headers_active = []
    banners_active = []
    for img in store.all_images:
        if img.image_type == 'header':
            headers_active.append(img)
        elif img.image_type == 'banner':
            banners_active.append(img)
    
    user = request.user
    favorites_ids = None
    
    # IDs de productos favoritos
    if user.is_authenticated:
        favorites_ids = get_favs_products(user)

    products = (
        Product.objects.filter(category__is_default=False, available=True, stock__gt=0)
        .values(*VALUES_CARDS_LIST)
        .order_by('price', 'id')[:100]    # limita a 100 la query
        .annotate(
            category_id=F("category__id"),
            subcategory_id=F("subcategory__id"),
            brand_id=F("brand__id"),
        )
    )
    
    # maybe in the future get categories with image_url to home
    categories = get_categories_n_subcategories(from_cache=True)
    brands = get_serializer_brands(values=('id', 'name', 'slug', 'image_url'))
    
    serializer = ProductListSerializer(products, many=True, context={'favorites_ids': favorites_ids})
    products_data = serializer.data
    
    # obtengo productos agrupados por category para renderizar en js
    products_by_category = {}
    for product in products_data:
        category_name = categories[product['category_id']]['category']['name']
        if category_name not in products_by_category:
            products_by_category[category_name] = []
        products_by_category[category_name].append(product)
        
    context = {
        'headers_active': headers_active,  
        'banners_active': banners_active,
        'products_json': json.dumps(products_by_category),
        'brands_json': json.dumps(brands),
        'categories': json.dumps(list(categories.values()))
    }

    return render(request, 'home/home.html', context)


def help_mp(request):
    from users.models import CustomUser
    users = CustomUser.objects.exclude(email__in=["lucascallamullo@hotmail.com", "lucascallamullo98@gmail.com"])
    return render(request, 'home/help_mp.html', {'users': users})







