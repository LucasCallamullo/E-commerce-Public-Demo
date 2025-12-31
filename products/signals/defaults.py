from django.db.models.signals import post_migrate
from django.dispatch import receiver

from products.models.category import Category
from products.models.subcategory import Subcategory
from products.models.brand import Brand


@receiver(post_migrate)
def create_defaults(sender, **kwargs):
    if sender.name != 'products':
        return

    Category.objects.get_or_create(
        is_default=True,
        defaults={
            'name': 'Sin categoría',
            'slug': 'sin-categoria',
        }
    )

    Subcategory.objects.get_or_create(
        is_default=True,
        defaults={
            'name': 'Sin Subcategoría',
            'slug': 'sin-subcategoria',
        }
    )

    Brand.objects.get_or_create(
        is_default=True,
        defaults={
            'name': 'Sin Marca',
            'slug': 'sin-marca',
        }
    )
