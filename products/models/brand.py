from django.db import models
from django.db.models import Q

from products.models.mixins import ProtectDefaultMixin

# El orden de herencia importa: poné ProtectDefaultMixin primero, antes de models.Model,
# para que su método save y delete tengan prioridad.
class Brand(ProtectDefaultMixin, models.Model):
    """
    Product Brand model.

    This model represents the brand associated with a product.  
    It supports a system-wide default brand, unique slugs, optional branding images,
    and default protection logic inherited from ProtectDefaultMixin.
    """

    # User-facing message must remain in Spanish
    protected_message = "No se puede modificar o eliminar la marca por defecto."

    # Basic fields
    name = models.CharField(max_length=32, unique=True)
    slug = models.SlugField(
        max_length=32,
        unique=True,
        null=True,
        blank=True
    )  # Optional unique slug
    image_url = models.URLField(null=True, blank=True)
    is_default = models.BooleanField(default=False)  # Marks the brand as the system default


    class Meta:
        """
        Meta configuration for constraints and indexes.

        Includes:
          - Unique non-null slug constraint.
          - Index on slug for optimized queries.
        """
        constraints = [
            models.UniqueConstraint(
                fields=['slug'],
                name='pbrand_unique_slug',
                condition=Q(slug__isnull=False)  # Applies only when slug is not null
            )
        ]

        indexes = [
            models.Index(
                fields=['slug'],
                name='pbrand_slug_idx',
                condition=Q(slug__isnull=False)
            )
        ]
