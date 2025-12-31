from django.urls import path
from products.views.api.product_api import ProductAPIView
from products.views.api.categories_api import CategoryAPIView, SubcategoryAPIView, BrandAPIView
from products.views.api.product_images_api import ProductImagesView


# ==============================================================================
#                        DRF API ENDPOINTS
# ==============================================================================
# NOTE for NAME URL on dtf we use -

urlpatterns = [
    # url para actualizar productos
    path('api/product/', ProductAPIView.as_view(), name='api_product_list_create'), # POST for create
    path('api/product/<int:product_id>/', ProductAPIView.as_view(), name='api_product_detail'), # GET, PUT, PATCH, DELETE
    
    # endpoints images    # url para actualizar imgenes
    path('products-images/<int:product_id>/', ProductImagesView.as_view(), name='prod-images'),
    path('api/product/<int:product_id>/images/', ProductImagesView.as_view(), name='product-images-api'),
    
    # urls endpoints para manejar category, subcategory, brand
    path('api/category/', CategoryAPIView.as_view(), name='pcategory-create-api'),  # POST for create
    path('api/category/<int:obj_id>/', CategoryAPIView.as_view(), name='pcategory-detail-api'),  # GET, PUT, PATCH, DELETE
    
    path('api/subcategory/', SubcategoryAPIView.as_view(), name='psubcategory-create-api'),  # POST for create
    path('api/subcategory/<int:obj_id>/', SubcategoryAPIView.as_view(), name='psubcategory-detail-api'),  # GET, PUT, PATCH, DELETE
    
    path('api/brand/', BrandAPIView.as_view(), name='pbrand-create-api'),  # POST for create
    path('api/brand/<int:obj_id>/', BrandAPIView.as_view(), name='pbrand-detail-api'),  # GET, PUT, PATCH, DELETE
]