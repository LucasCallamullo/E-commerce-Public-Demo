from django.urls import path
from products.views.api.product_api import ProductAPIView
from products.views.api.catalog_api import CategoryAPIView, SubcategoryAPIView, BrandAPIView
from products.views.api.product_images_api import ProductImagesView


# ==============================================================================
#                        DRF API ENDPOINTS
# ==============================================================================
urlpatterns = [
    # ----------------------- Product
    path('api/products/', ProductAPIView.as_view(), name='api_products'), # POST, GET
    path('api/products/<int:pk>/', ProductAPIView.as_view(), name='api_products_detail'), # GET, PUT, PATCH, DELETE
    
    # ----------------------- Product Images
    path('api/products/<int:product_id>/images/', 
        ProductImagesView.as_view(), name='api_product_images'), # GET, POST, DELETE
    
    # ----------------------- Category
    path('api/categories/', CategoryAPIView.as_view(), name='api_categories'), # POST, GET
    path('api/categories/<int:pk>/', 
        CategoryAPIView.as_view(), name='api_categories_detail'),  # GET, PUT, PATCH, DELETE
    
    # ----------------------- Subcategory
    path('api/subcategories/', SubcategoryAPIView.as_view(), name='api_subcategories'), # POST, GET
    path('api/subcategories/<int:pk>/', 
        SubcategoryAPIView.as_view(), name='api_subcategories_detail'),  # GET, PUT, PATCH, DELETE
    
    # ----------------------- Brand
    path('api/brands/', BrandAPIView.as_view(), name='api_brands'), # POST, GET
    path('api/brands/<int:pk>/', 
        BrandAPIView.as_view(), name='api_brands_detail'),  # GET, PUT, PATCH, DELETE
]