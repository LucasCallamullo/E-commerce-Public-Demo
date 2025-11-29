

from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver

from products.models import PCategory


@receiver(pre_save, sender=PCategory)  # This decorator registers the function as a pre_save signal for the PCategory model
def protect_default(sender, instance, **kwargs):
    
    # Signal that executes BEFORE saving a category.

    # Check if the instance is the default category AND it's not a new creation
    if instance.is_default and not instance._state.adding:
        
        # Get the original version of the category from the database
        original = PCategory.objects.get(pk=instance.pk)
        
        # Check if any of these critical fields have changed:
        # - name: category name
        # - slug: unique URL identifier
        if any(getattr(original, f) != getattr(instance, f) for f in ['name', 'slug']):
            # If changes are detected in name or slug, raise an error
            raise ValueError("No se puede modificar la categoría default")

        

@receiver(pre_delete, sender=PCategory)  # Decorator for pre_delete signal
def protect_default_deletion(sender, instance, **kwargs):
    
    # Signal that executes BEFORE deleting a category.
    
    # Check if the instance is the default category
    if instance.is_default:
        # If it's the default category, raise an error to prevent deletion
        raise ValueError("No se puede eliminar la categoría default")
    










""" 
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from products.models import ProductImage

@receiver(post_save, sender=ProductImage)
def refresh_main_image_on_save(sender, instance, **kwargs):
    # Product = instance.product, Is Main Saved ? instance.main_image , get url instance.image_url   
    if instance.main_image: 
        # instance.product.update_main_image_url(instance.image_url)
"""