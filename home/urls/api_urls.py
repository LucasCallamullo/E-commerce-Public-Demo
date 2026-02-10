from django.urls import path
from home.views.api.store import StoreAPI
from home.views.api.store_image import StoreImageAPI
from home.views.api.social_media import SocialMediaAPI


urlpatterns = [
    # --- Store Endpoints ---
    path('api/stores/', StoreAPI.as_view(), 
        name='api_stores'), # GET List
    
    path('api/stores/<int:pk>/', StoreAPI.as_view(), 
        name='api_stores_detail'), # GET (detail), PATCH
    
    # --- Store Images Endpoints ---
    path('api/stores/<int:store_id>/images/', StoreImageAPI.as_view(), 
        name='api_store_images'), # GET List, POST
    
    path('api/stores/<int:store_id>/images/<int:image_id>/', StoreImageAPI.as_view(), 
        name='api_store_images_detail'),     # GET (detail), PATCH, DELETE
    
    # --- Social Networks Endpoints ---
    path('api/stores/<int:store_id>/social-networks/', SocialMediaAPI.as_view(), 
        name='api_store_networks'), # GET List, POST

    path('api/stores/<int:store_id>/social-networks/<int:network_id>/', SocialMediaAPI.as_view(), 
        name='api_store_networks_detail'), # GET (detail), PATCH, DELETE
]