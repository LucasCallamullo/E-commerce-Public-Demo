from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_migrate

import logging
logger = logging.getLogger(__name__)

# Por algun motivo que nadie sabe tengo que importar esto antes que cualquier cosa
# dentro del signal para que no tire error al iniciar
from products.models.product import Product
from products.models.brand import Brand
from products.models.category import Category
from products.models.subcategory import Subcategory
    
@receiver(post_migrate)
def create_defaults(sender, **kwargs):
    
    if sender.name != 'products':
        return
    
    # Intentamos buscarlo primero
    if not Category.objects.filter(is_default=True).exists():
        obj = Category(name='Sin categoría', slug='sin-categoria', is_default=True)
        # Llamada directa al método de la clase base de Django
        models.Model.save(obj)
        logger.debug('[CREATE by models.Model] Category')
        
        if not Category.objects.filter(is_default=True).exists():
            obj = Category(name='Sin categoría', slug='sin-categoria', is_default=True)
            
            # LLAMADA CLAVE: Saltamos los Mixins y vamos directo a la persistencia de Django
            super(Category, obj).save()
            logger.debug('[CREATE by super(Category, obj)] Category')
            
            
    # Intentamos buscarlo primero
    if not Brand.objects.filter(is_default=True).exists():
        obj = Brand(name='Sin Marca', slug='sin-marca', is_default=True)
        # Llamada directa al método de la clase base de Django
        models.Model.save(obj)
        logger.debug('[CREATE by models.Model] Brand')
        
        if not Brand.objects.filter(is_default=True).exists():
            obj = Brand(name='Sin Marca', slug='sin-marca', is_default=True)
            
            # LLAMADA CLAVE: Saltamos los Mixins y vamos directo a la persistencia de Django
            super(Brand, obj).save()
            logger.debug('[CREATE by super(Brand, obj)] Category')
        