"""
URL configuration for ecommerce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

# solo funciona con debug = False es para manejar erorres
handler403 = 'core.views.exceptions.rate_limit_view'

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Django Tradicional
    path('', include("core.urls.api_urls")),    # DRF
    path('', include("core.urls.swagger_docs")),
    
    path('', include("home.urls.api_urls")),
    path('', include("home.urls.html_urls")),
    
    path('', include("users.urls.html")),
    path('', include("users.urls.api")),    # DRF
    
    path('', include("cart.urls.html_urls")),
    path('', include("cart.urls.api_urls")),
    
    path('', include("products.urls.html_urls")),
    path('', include("products.urls.api_urls")),    # DRF
    
    path('', include("dashboard.urls")),
    path('', include("dashboard_sales.urls")),
    
    path('', include("profiles.urls")),
    
    path('', include("favorites.urls")),
    
    path('', include("orders.urls.api_urls")),    # DRF
    path('', include("orders.urls.html_urls")),
    
    path('', include("payments.urls")),
    
    path('', include("contact.urls")),
]


# eliminar en producion
from django.conf import settings
from django.conf.urls.static import static

# Esto solo funciona en desarrollo (DEBUG=True)
# En producción (VPS), Nginx se encargará de esto de forma más eficiente
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    """    Es solo para desarrollo ver despues en local
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns 
    """