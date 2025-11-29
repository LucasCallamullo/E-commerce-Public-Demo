

from django.urls import path
from products.views_api import *


# ==============================================================================
#                        DRF API ENDPOINTS
# ==============================================================================
# NOTE for NAME URL on dtf we use -

urlpatterns = [
    
    # endpoints images 
    path('products-images/<int:product_id>/', ProductImagesView.as_view(), name='prod-images'),

    # url para actualizar productos
    path('api/product/', ProductAPIView.as_view(), name='product-create-api'), # POST for create
    path('api/product/<int:product_id>/', ProductAPIView.as_view(), name='product-update-api'), # GET, PUT, PATCH, DELETE
    
    # url para actualizar imgenes
    path('api/product/<int:product_id>/images/', ProductImagesView.as_view(), name='product-images-api'),
    
    # generic endpoint to upload images for any model except Product
    path('api/upload/image', GenericUploadImageAPIView.as_view(), name='upload-images-api'),
    
    # urls endpoints para manejar category, subcategory, brand
    path('api/category/', PCategoryAPIView.as_view(), name='pcategory-create-api'),  # POST for create
    path('api/category/<int:obj_id>/', PCategoryAPIView.as_view(), name='pcategory-detail-api'),  # GET, PUT, PATCH, DELETE
    
    path('api/subcategory/', PSubcategoryAPIView.as_view(), name='psubcategory-create-api'),  # POST for create
    path('api/subcategory/<int:obj_id>/', PSubcategoryAPIView.as_view(), name='psubcategory-detail-api'),  # GET, PUT, PATCH, DELETE
    
    path('api/brand/', PBrandAPIView.as_view(), name='pbrand-create-api'),  # POST for create
    path('api/brand/<int:obj_id>/', PBrandAPIView.as_view(), name='pbrand-detail-api'),  # GET, PUT, PATCH, DELETE
    
]