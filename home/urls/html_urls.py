

from django.urls import path

from home.views.html.home import home, help_mp

urlpatterns = [
    path('', home, name='Home'),
    path('help_mp/', help_mp, name='help_mp'),
    
]
