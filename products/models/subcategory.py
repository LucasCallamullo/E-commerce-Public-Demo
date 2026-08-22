from django.db import models, transaction
from products.models.category import Category
from products.models.mixins import FileCleanupMixin, SlugFieldMixin

import logging
logger = logging.getLogger(__name__)

def get_default_category_id() -> int:
    """
    Retrieves the primary key of the default Category. 
    Returning only the integer ID.
    """
    return Category.objects.filter(is_default=True).values_list('id', flat=True).first()


class Subcategory(FileCleanupMixin, SlugFieldMixin, models.Model):
    """
    Product Subcategory model.
    
    Data Integrity Design:
    - Scoped Uniqueness: Names/Slugs are unique within their parent Category.
    - Orphan Protection: Managed via 'pre_delete' signals for intelligent renaming 
      and reassignment to the default category during parent deletion.
    - Constraint: 'DO_NOTHING' on delete ensures the signal has full control, 
      while DB-level FK constraints prevent orphaned records.
    """
    # Basic fields
    name = models.CharField(max_length=32)  # Unique per category, not globally
    slug = models.SlugField(max_length=32, null=True, blank=True)
    
    # Relations
    category = models.ForeignKey(
        'Category', 
        on_delete=models.DO_NOTHING,
        related_name="subcategories"
    )
    
    # CharField is used instead of ImageField for architectural design reasons:
    # 1. Decoupling: Separates storage logic from the model. The path is managed 
    #    externally (API/Services), facilitating future migrations to CDNs or Cloud Storage (S3).
    # 2. Performance (Nginx): Enables Nginx to serve files directly as static resources 
    #    via 'alias', bypassing the Django/Python overhead for high-performance delivery.
    # 3. Efficiency: Avoids Django's automatic file-system validations, which can be 
    #    resource-intensive during Bulk Load operations, and simplifies intelligent URL handling.
    image_url = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return f"Subcategory: {self.name} | ID: {self.id}"
    
    def __init__(self, *args, **kwargs):
        """
        Initializes the Subcategory instance and captures the initial parent Category.
        
        A snapshot of the category_id is stored to detect parental shifts during 
        the save lifecycle, allowing for cascading updates to related products.
        """
        super().__init__(*args, **kwargs)
        
        # Internal snapshot to monitor parent Category changes without SQL overhead.
        self._category_id = self.__dict__.get('category_id')


    def save(self, *args, **kwargs):
        """
        Enforces structural integrity and synchronizes child Products upon parent changes.
        
        Workflow:
            1. Proactive Assignment: If a new Subcategory lacks a Category, assign the system default.
            2. Persistence: Commit changes to the database.
            3. Cascading Update: If the parent Category has changed, perform a bulk update on 
               all associated Products to maintain the Grandparent -> Parent -> Child hierarchy.
        """
        with transaction.atomic():
            # Step 1: Handle orphaned Subcategories during creation.
            # Direct category_id check avoids triggering a JOIN/Select query on self.category.
            if not self.pk and self.category_id is None:
                default_id = get_default_category_id()
                if default_id:
                    self.category_id = default_id
                    # Initialize snapshot with default for consistent change detection.
                    self._category_id = default_id
        
            # Step 2: Database persistence.
            saved = super().save(*args, **kwargs)
        
            # Step 3: Relational Synchronization (Update Logic).
            # Triggered only if the Subcategory is moved to a different Category.
            current_cat_id = self.__dict__.get('category_id')
            
            logger.debug(
                'Sync Check - PK: %s | Snapshot Cat: %s | Current Cat: %s', 
                self.pk, self._category_id, current_cat_id
            )

            if self.pk and self._category_id and self._category_id != current_cat_id:
                from products.models.product import Product
                
                # Perform a bulk SQL update for performance. 
                # This ensures all Products 'follow' the Subcategory to its new parent Category.
                updated_count = (
                    Product.objects.filter(subcategory_id=self.id)
                    .update(category_id=current_cat_id)
                )
                
                logger.info(
                    "Cascading Sync: Subcategory %s moved to Category %s. %s products updated.",
                    self.id, current_cat_id, updated_count
                )
                
                # Update snapshot to reflect the new persisted state.
                self._category_id = current_cat_id

            return saved

    class Meta:
        """
        Meta configuration for database constraints and indexes.

        Design Decisions:
        - Scope Uniqueness: Both name and slug are unique ONLY within the same category.
          This allows repeating common subcategory names (e.g., 'Others', 'Sales') 
          across different parent categories.
        - Performance: Implicit indexes from UniqueConstraints are leveraged to 
          avoid redundant index creation, reducing disk I/O and storage.
        - Partial Indexing: Slugs are indexed and constrained only when not null 
          to support optional subcategory paths.
        """
        verbose_name = "Subcategory"
        verbose_name_plural = "Subcategories"
        constraints = [
            # Unique name ONLY within its parent category
            # Prevent duplicate names under the same category
            models.UniqueConstraint(
                fields=['name', 'category'],
                name='psubcategory_unique_name_per_category'
            ),
            
            # Unique slug ONLY within its parent category (Partial Constraint)
            # Allows /electronics/sales/ and /clothing/sales/
            # Enforce slug uniqueness on parent category only when slug is not null
            models.UniqueConstraint(
                fields=['slug', 'category'],
                name='psubcategory_unique_slug_per_category',
                condition=models.Q(slug__isnull=False)
            ),
        ]

        indexes = [
            # 3. Composite Index for URL resolution
            # Optimized for queries like: Subcategory.objects.get(category_id=X, slug='Y')
            models.Index(
                fields=['category', 'slug'],
                name='psubcategory_cat_slug_idx',
                condition=models.Q(slug__isnull=False),
            ),
        ]
            # Este indice se crea por defecto al definir el constraint de arriba
            # name: psubcategory_unique_name_per_category
            
            # Common filtering pattern: category + name
            # models.Index(
            #    fields=['category', 'name'],
            #    name='psubcategory_category_name_idx'
            # )
