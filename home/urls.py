

from django.urls import path
# from django.conf import settings
# from django.conf.urls.static import static

from home import views

urlpatterns = [
    path('', views.home, name='Home'),
    path('help_mp/', views.help_mp, name='help_mp'),
    
] # + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 


