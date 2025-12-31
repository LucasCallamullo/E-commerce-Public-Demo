from django.db import models

from products.models.mixins import ProtectDefaultMixin
from products.models.category import Category


def get_default_category_id():
    return Category.objects.get(is_default=True).id


# El orden de herencia importa: poné ProtectDefaultMixin primero, antes de models.Model,
# para que su método save y delete tengan prioridad.
class Subcategory(ProtectDefaultMixin, models.Model):
    """
    Product Subcategory model.

    This model represents a second-level classification within a product
    category. Each subcategory belongs to exactly one category and can also
    declare itself as a protected default instance.
    """

    # User-facing message must remain in Spanish
    protected_message = "No se puede modificar o eliminar la sub-categoría por defecto."

    # Basic fields
    name = models.CharField(max_length=32)  # Unique per category, not globally
    slug = models.SlugField(max_length=32, null=True, blank=True)  # Optional slug
    image_url = models.URLField(null=True, blank=True)
    is_default = models.BooleanField(default=False)

    # Relations
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_DEFAULT,
        default=get_default_category_id,
        related_name="subcategories"
    )

    class Meta:
        """
        Meta configuration for database constraints and indexes.

        This includes:
          - Unique name within the same category.
          - Unique non-null slug.
          - Ensuring only one default subcategory exists per category.
          - Indexes on slug and (category, name) for faster filtering.
        """
        constraints = [
            # Prevent duplicate names under the same category
            models.UniqueConstraint(
                fields=['name', 'category'],
                name='psubcategory_unique_name_per_category'
            ),

            # Enforce slug uniqueness only when slug is not null
            models.UniqueConstraint(
                fields=['slug'],
                name='psubcategory_unique_non_null_slug',
                condition=models.Q(slug__isnull=False)
            ),

            # Ensure only one default subcategory per category
            models.UniqueConstraint(
                fields=['category'],
                condition=models.Q(is_default=True),
                name='psubcategory_unique_default_per_category'
            )
        ]

        indexes = [
            # Faster slug lookups
            models.Index(
                fields=['slug'],
                name='psubcategory_slug_idx',
                condition=models.Q(slug__isnull=False),
            ),
            # Common filtering pattern: category + name
            models.Index(
                fields=['category', 'name'],
                name='psubcategory_category_name_idx'
            )
        ]

        # User-facing naming stays in Spanish
        verbose_name = 'Subcategoría de Producto'
        verbose_name_plural = 'Subcategorías de Productos'
