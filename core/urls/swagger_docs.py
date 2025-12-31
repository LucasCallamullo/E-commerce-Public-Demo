

from django.urls import path

# Importaciones de drf-spectacular
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # DOCUMENTACIÓN DE API
    # 1. Schema YAML/JSON (para herramientas)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # 2. Interfaz Swagger UI (la que más usarás)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # 3. Interfaz Redoc (alternativa más limpia)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
