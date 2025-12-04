

from django.urls import path
from favorites.views import ToggleFavoriteProduct


urlpatterns = [
    path('products/toggle-favorite/<int:product_id>/', ToggleFavoriteProduct.as_view(), name='toggle-favorite'),

]

