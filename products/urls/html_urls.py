from django.urls import path
from products.views.html import views

urlpatterns = [
    path('reset_stocks/', views.reset_stocks, name='reset_stocks'),
    
    # filters to product_list.html
    path('productos/', views.product_list, name='product_list'),
    
    # SEO friendly category paths
    path('productos/categoria/<slug:cat_slug>/', 
        views.product_list, name='product_list_category'),
    
    path('productos/categoria/<slug:cat_slug>/<slug:subcat_slug>/', 
        views.product_list, name='product_list_subcategory'),

    # Brand paths
    path('productos/marca/<slug:brand_slug>/', views.product_list, name='product_list_brand'),
    
    # Search (Usually a GET query param like ?q=iphone)
    path('productos/buscar/', views.product_list, name='product_search'),
    path('producto/busqueda/', views.product_list, name='product_top_search'),
   
    # url for product_detail.html - Standard e-commerce practice:
    path('<int:product_id>-<slug:slug>/', views.product_detail, name='product_detail'),
]
