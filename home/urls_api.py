

from django.urls import path
from home.views_api import *

urlpatterns = [
    # drf endpoints
    path('api/store/<int:store_id>/', StoreAPI.as_view(), name='update_store'),
    
     # ?image_type=header # GET (list), POST (create)
    path('api/store-images/<int:store_id>/<str:image_type>/', StoreImageAPI.as_view(), name='api_images'), 
    # GET (detail), PATCH, DELETE
    path('api/store-images/<int:store_id>/<str:image_type>/<int:image_id>/', StoreImageAPI.as_view(), name='api_image_detail'), 
]