from django.db import models
from django.db.models import Q

from products.models.mixins import ProtectDefaultMixin, FileCleanupMixin, SlugFieldMixin

# En Python, el orden en que declaras las clases en la herencia define el Method Resolution Order (MRO).
# Por eso el orden de los save() o delete() primero llaman a ProtectDefaultMixin y después a models.Model
class Category(FileCleanupMixin, SlugFieldMixin, ProtectDefaultMixin, models.Model):
    """
    Product Category model.

    This model represents a top-level product category and includes:
      - a human-readable 'name'
      - an optional 'slug' (URL-safe identifier)
      - an optional image URL
      - an 'is_default' flag to mark a protected default instance

    Responsibilities:
      - Provide a convenient method to obtain or create the system default category.
      - Enforce uniqueness constraints for non-null slugs.
      - Expose a concise string representation.
    """
    protected_message = "No se puede modificar o eliminar la Categoría por defecto."

    # Basic fields
    name = models.CharField(max_length=32, unique=True)
    slug = models.SlugField(max_length=32, unique=True, null=True, blank=True)
    
    # CharField is used instead of ImageField for architectural design reasons:
    # 1. Decoupling: Separates storage logic from the model. The path is managed 
    #    externally (API/Services), facilitating future migrations to CDNs or Cloud Storage (S3).
    # 2. Performance (Nginx): Enables Nginx to serve files directly as static resources 
    #    via 'alias', bypassing the Django/Python overhead for high-performance delivery.
    # 3. Efficiency: Avoids Django's automatic file-system validations, which can be 
    #    resource-intensive during Bulk Load operations, and simplifies intelligent URL handling.
    image_url = models.CharField(max_length=200, blank=True, null=True)
    
    # Marks the brand as the system default
    is_default = models.BooleanField(default=False)

    class Meta:
        """
        Database-level constraints and indexes for the category model.

        Notes:
            - The unique constraint and index on 'slug' apply only when slug is non-null.
            - Using `Q(slug__isnull=False)` avoids enforcing uniqueness/indexing on rows
              where the slug is intentionally left null.
        """
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        constraints = [
            models.UniqueConstraint(
                fields=['slug'],
                name='pcategory_unique_slug',
                condition=Q(slug__isnull=False)
            )
        ]
        indexes = [
            models.Index(
                fields=['slug'],
                name='pcategory_slug_idx',
                condition=Q(slug__isnull=False)
            )
        ]

    def __str__(self):
        return f"Category: {self.name} | ID: {self.id}"