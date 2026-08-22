from django.db import transaction
from django.db.models import Q
from django.dispatch import receiver
from django.db.models.signals import pre_delete

import logging
logger = logging.getLogger(__name__)

@receiver(pre_delete, sender='products.Category')
def handle_subcategory_collision(sender, instance, **kwargs):
    """
    Prevents IntegrityErrors during Category deletion by preemptively reassigning 
    orphaned Subcategories to the 'is_default' Category.
    
    If a name collision occurs (the default category already has a subcategory 
    with the same name), the moving subcategory is renamed to 'OriginalName (ParentCategory)'.
    """
    if instance.is_default:
        return
    
    from products.models.mixins import SlugFieldMixin
    from products.models.category import Category
    from products.models.subcategory import Subcategory
    
    with transaction.atomic():
        # 1. Fetch all involved subcategories in a single optimized query.
        # I include current children and potential siblings in the target default category.
        all_subs = list(
            Subcategory.objects
            .filter(Q(category__is_default=True) | Q(category_id=instance.id))
            .select_related('category')
            .only(
                'id', 'name', 'slug', 'category_id', 
                'category__id', 'category__name', 'category__is_default'
            )
        )

        # 2. Extract the default category ID from the query result.
        # Using 'next' with a generator for O(1) efficiency in memory.
        default_id = next((s.category.id for s in all_subs if s.category.is_default), None)
        
        # 3. Filter subcategories to be moved in-memory.
        to_move = [s for s in all_subs if s.category_id == instance.id]
        if not to_move:
            # si no hay nada que modificar retorno
            logger.info('No hay Subcategorías asociadas a %s', sender.__name__)
            return
        
        # CASE: Default category exists but has no children.
        # We perform a direct SQL update and exit as no collisions are possible.
        if not default_id:
            default = Category.objects.filter(is_default=True).only('id').first()
            logger.info('Se busco DEFAULT CATEGORY %s', default.id)
            if not default:
                logger.error('System Integrity Error: Default Category not found.')
                return
            
            # We move the subcategories in bulk_update, preserving their name and slug
            Subcategory.objects.filter(category_id=instance.id).update(category_id=default.id)
            return
        
        # 4. Conflict Resolution Logic.
        # I create a set with the names of the subcategories that belong to default
        existing_names = { s.name for s in all_subs if s.category.is_default }
        modified_subs = []
        
        for sub in to_move:
            # Manually reassign parent before the DB-level SET_DEFAULT takes effect.
            sub.category_id = default_id
            
            # If name exists in the target category, rename to avoid UniqueConstraint failure.
            if sub.name in existing_names:
                # Usamos método estático para el slug
                new_name = f"{sub.name} ({instance.name})"
                sub.name = new_name[:32]  # Truncate to match max_length
                sub.slug = SlugFieldMixin.get_new_slug(name=sub.name)
                logger.info('Collision resolved: %s renamed to %s', sub.id, sub.name)
            
            modified_subs.append(sub)

        # 5. Persist all changes in a single database round-trip.
        if modified_subs:
            logger.info('Migrating %s subcategories from %s.', len(modified_subs), instance.name)
            Subcategory.objects.bulk_update(modified_subs, ['name', 'slug', 'category_id'])
        
        # At this point, Django proceeds to delete the Category.
        # Since relations were moved, the DB-level 'SET_DEFAULT' has no work left to do.
    