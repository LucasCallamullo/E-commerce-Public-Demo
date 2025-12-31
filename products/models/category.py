from django.db import models
from django.db.models import Q

from products.models.mixins import ProtectDefaultMixin

# El orden de herencia importa: poné ProtectDefaultMixin primero, antes de models.Model,
# para que su método save y delete tengan prioridad.
class Category(ProtectDefaultMixin, models.Model):
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
    # User-facing message must remain in Spanish
    protected_message = "No se puede modificar o eliminar la categoría por defecto."

    # Basic fields
    name = models.CharField(max_length=32, unique=True)
    slug = models.SlugField(max_length=32, unique=True, null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        """
        Database-level constraints and indexes for the category model.

        Notes:
            - The unique constraint and index on 'slug' apply only when slug is non-null.
            - Using `Q(slug__isnull=False)` avoids enforcing uniqueness/indexing on rows
              where the slug is intentionally left null.
        """
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

