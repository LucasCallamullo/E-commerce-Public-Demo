
from django.shortcuts import render

# capaz en el futuro mover como servicio a core
from home.services.store import StoreService
from home.services.store_image import StoreImageService

from products.models.product import Product
from products.services.product import ProductService
from products.services.category import CategoryService
from products.services.brand import BrandService


def home(request):
    """
    Main entry point for the store's landing page.
    
    This view orchestrates the data retrieval from multiple specialized services 
    to build the home screen context. It prioritizes cached data for high 
    performance, ensuring minimal database interaction.

    The view context includes:
    - Marketing images (headers and banners).
    - Grouped products by category for specialized sections.
    - Global lists of brands and categories.
    - Curated product lists (general and discounted offers).

    Args:
        request: The Django HttpRequest object.

    Returns:
        HttpResponse: Rendered 'home/home.html' template with the full context.
    """
    # 1. Retrieve store configuration and marketing assets (Cached)
    store = StoreService.get_public_store(store_id=1)
    store_images = StoreImageService.get_home_active_images(store_id=store.get('id', 1))
    
    # 2. Fetch curated product data (includes 'is_favorite' flag if user is logged in)
    # This service method likely hits the cache for the bulk of product data.
    data_products = ProductService.get_home_data(user=request.user)
    
    # 3. Fetch master lists for navigation and filtering (Cached)
    categories = CategoryService.get_categories_list()
    brands = BrandService.get_brands_list()
    
    # 4. Process data in memory to group products by category for UI sections
    products_by_category = CategoryService.get_products_by_category(
        products=data_products['products'],
        categories=categories
    )
    
    context = {
        'headers': store_images.get('headers', []),
        'banners': store_images.get('banners', []),
        'brands': brands,
        'categories': categories,
        'products_by_category': products_by_category,
        'products': data_products['products'],
        'products_offer': data_products['offers']
    }

    return render(request, 'home/home.html', context)


def help_mp(request):
    from users.models import CustomUser
    users = CustomUser.objects.exclude(email__in=["lucascallamullo@hotmail.com", "lucascallamullo98@gmail.com"])
    return render(request, 'home/help_mp.html', {'users': users})