from django.db import models
from django.db.models import Q

from products.models.mixins import ProtectDefaultMixin, SlugFieldMixin, FileCleanupMixin

# El orden de herencia importa: poné ProtectDefaultMixin primero, antes de models.Model,
# para que su método save y delete tengan prioridad.
class Brand(FileCleanupMixin, SlugFieldMixin, ProtectDefaultMixin, models.Model):
    """
    Product Brand model.

    This model represents the brand associated with a product.  
    It supports a system-wide default brand, unique slugs, optional branding images,
    and default protection logic inherited from ProtectDefaultMixin.
    """
    protected_message = "No se puede modificar o eliminar la Marca por defecto."

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
        Meta configuration for constraints and indexes.

        Includes:
          - Unique non-null slug constraint.
          - Index on slug for optimized queries.
        """
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'
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

    def __str__(self):
        return f"Brand: {self.name} | ID: {self.id}"