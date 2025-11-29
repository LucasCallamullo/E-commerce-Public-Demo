from django.urls import path
from products import views


urlpatterns = [
    path('reset_stocks/', views.reset_stocks, name='reset_stocks'),
    
    # filters to product_list.html
    path('productos-lista/', views.product_list, name='product_list'),
    path('productos/<slug:cat_slug>/', views.product_list, name='pl_category'),
    path('productos/<slug:cat_slug>/<slug:subcat_slug>/', views.product_list, name='pl_subcategory'),
    path('marca/<slug:brand_slug>/', views.product_list, name='pl_brand'),
    path('producto/busqueda/', views.product_list, name='product_top_search'),
   
    # url for product_detail.html
    path('<int:product_id>-<slug:slug>/', views.product_detail, name='product_detail'),
]
