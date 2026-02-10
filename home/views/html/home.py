
from django.shortcuts import render

# capaz en el futuro mover como servicio a core
from home.services.store import StoreService
from home.services.store_image import StoreImageService

from products.models.product import Product
from products.services.product import ProductService
from products.services.category import CategoryService
from products.services.brand import BrandService


def home(request):
    
    # obtener headers y banners dsde el servicio
    store = StoreService.get_public_store(store_id=1)
    store_images = StoreImageService.get_home_active_images(store_id=store.get('id', 1))
    
    # retorna una lista de diccionarios de los productos -> list[{}, {}, {}]
    products = ProductService.for_home(user=request.user)
    
    # maybe in the future get categories with image_url to home
    categories = CategoryService.for_cards(from_cache=True)
    brands = BrandService.for_cards(brand_ids=None)
    
    # obtengo productos agrupados por category para renderizar en js
    # Crear diccionario mejorado: id -> {name, slug}
    category_map = {
        c["category"]["id"]: {
            "name": c["category"]["name"],
            "slug": c["category"]["slug"],  # ¡IMPORTANTE!
            "id": c["category"]["id"]
        }
        for c in categories
    }
        
    # Agrupar productos con info completa de categoría
    products_by_category = {}
    for p in products:
        cat_info = category_map.get(p["category_id"])
        if not cat_info:
            continue
        
        # Usar slug como key (o id)
        key = cat_info["id"]  # "electronica"
        
        if key not in products_by_category:
            products_by_category[key] = {
                "name": cat_info["name"],
                "slug": cat_info["slug"],
                "id": cat_info["id"],
                "products": []
            }
        
        products_by_category[key]["products"].append(p)
        
    products_offer = Product.objects.filter(available=True, discount_ars__gt=0)
        
    context = {
        'headers': store_images.get('headers', []),
        'banners': store_images.get('banners', []),
        'products_by_category': products_by_category,
        'brands': brands,
        'categories': categories,
        'products': products,
        'products_offer': products_offer
    }

    return render(request, 'home/home.html', context)


def help_mp(request):
    from users.models import CustomUser
    users = CustomUser.objects.exclude(email__in=["lucascallamullo@hotmail.com", "lucascallamullo98@gmail.com"])
    return render(request, 'home/help_mp.html', {'users': users})