

from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver

from products.models.category import Category
from products.models.product import Product

from django.contrib.postgres.search import SearchVector

from core.utils.utils_basic import normalize_or_None
from django.utils.text import slugify

"""
@receiver(pre_save, sender=Product)
def product_pre_save(sender, instance, **kwargs):
    
    Pre-save signal for the Product model.

    This signal ensures that certain fields are automatically updated
    before a Product instance is saved. It handles three main tasks:

    1. Slug Generation:
       - If the Product has a 'name', a slug is automatically generated
         from the name using Django's 'slugify'.
       - Example: "Cable HDMI 5mts" -> "cable-hdmi-5mts"
       - This is stored in 'instance.slug'.

    2. Normalization of Product Name:
       - The 'normalized_name' field is populated by normalizing the 'name'.
       - The normalization is performed using the 'normalize_or_None' function,
         which typically:
            * Converts text to lowercase
            * Removes accents and special characters
            * Replaces multiple spaces with a single space
       - This ensures consistent internal search behavior.

    3. Search Vector Update (PostgreSQL Full-Text Search):
       - For new products (no primary key yet):
           * The 'search_vector' field is initialized with a SearchVector
             of the normalized_name, using weight='A' for high relevance.
       - For existing products (with a primary key):
           * Fetch the current 'normalized_name' from the database.
           * If it has changed compared to the instance about to be saved,
             recalculate the 'search_vector' with the updated normalized_name.
       - This ensures that the PostgreSQL full-text search vector is always
         in sync with the normalized name.

    Notes:
    - The signal only triggers for Product instances.
    - Bulk updates bypass signals, so this signal does not run when using
      'bulk_update'. For existing products, you must recalculate
      'search_vector' manually if needed.
    - The weight='A' in SearchVector indicates highest importance for ranking.

    Args:
        sender (Model class): The model class sending the signal (Product)
        instance (Product): The actual instance being saved
        **kwargs: Additional keyword arguments passed by Django signals
    
    if instance.name:
        # Generate SEO-friendly slug and normalized name
        instance.slug = slugify(instance.name)
        instance.normalized_name = normalize_or_None(instance.name)

    # New instance: initialize search_vector
    if not instance.pk:
        instance.search_vector = SearchVector('normalized_name', weight='A')
        return

    # Existing instance: check if normalized_name changed
    old = Product.objects.filter(pk=instance.pk).values('normalized_name').first()
    if old and old['normalized_name'] != instance.normalized_name:
        instance.search_vector = SearchVector('normalized_name', weight='A')
        
"""

    

"""

@receiver(pre_save, sender=Category)  # This decorator registers the function as a pre_save signal for the Category model
def protect_default(sender, instance, **kwargs):
    
    # Signal that executes BEFORE saving a category.

    # Check if the instance is the default category AND it's not a new creation
    if instance.is_default and not instance._state.adding:
        
        # Get the original version of the category from the database
        original = Category.objects.get(pk=instance.pk)
        
        # Check if any of these critical fields have changed:
        # - name: category name
        # - slug: unique URL identifier
        if any(getattr(original, f) != getattr(instance, f) for f in ['name', 'slug']):
            # If changes are detected in name or slug, raise an error
            raise ValueError("No se puede modificar la categoría default")

        

@receiver(pre_delete, sender=Category)  # Decorator for pre_delete signal
def protect_default_deletion(sender, instance, **kwargs):
    
    # Signal that executes BEFORE deleting a category.
    
    # Check if the instance is the default category
    if instance.is_default:
        # If it's the default category, raise an error to prevent deletion
        raise ValueError("No se puede eliminar la categoría default")
    


 
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from products.models import ProductImage

@receiver(post_save, sender=ProductImage)
def refresh_main_image_on_save(sender, instance, **kwargs):
    # Product = instance.product, Is Main Saved ? instance.main_image , get url instance.image_url   
    if instance.main_image: 
        # instance.product.update_main_image_url(instance.image_url)
"""