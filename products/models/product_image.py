from django.db import models


class ProductImage(models.Model):
    """
    Represents an image linked to a product.

    A product may have multiple images, but exactly one can be designated
    as the main image. This model manages individual image records as well
    as helper logic that automatically updates the main image selection.
    """
    product = models.ForeignKey(
        "Product", on_delete=models.CASCADE, related_name='images', 
        help_text="The product this image belongs to.")
    
    image_url = models.URLField(
        null=True, blank=True, help_text="URL of the image.")
    
    main_image = models.BooleanField(
        default=False, help_text="Indicates whether this is the product's main image.")

    def update_main_image(self, images_list=None):
        """
        Set this image as the product's main image.

        If a list of prefetched images is provided, other images belonging
        to the same product will be updated efficiently without triggering
        extra database queries.

        Args:
            images_list (Iterable[ProductImage] | None):
                Optional list or queryset of the product's images.
                If provided, it avoids performing an additional fetch
                to unset other main images.
        """
        if images_list is not None:
            other_ids = [img.id for img in images_list if img.id != self.id]
            if other_ids:
                ProductImage.objects.filter(id__in=other_ids).update(main_image=False)

        self.main_image = True
        self.save(update_fields=['main_image'])

    def delete(self, *args, **kwargs):
        """
        Delete the image instance.

        If the deleted image was the product's main image, the method will:
          - Select a new main image (first available).
          - Update the product's `main_image` field accordingly.
        """
        is_main = self.main_image
        product = self.product if is_main else None

        super().delete(*args, **kwargs)

        # If the deleted image was the main one, assign a new main image
        if product:
            new_main = product.images.first()
            if new_main:
                new_main.update_main_image()
                product.update_main_image(new_main.image_url)

    def __str__(self):
        """Readable representation of the image entry."""
        return f"Url: {self.image_url} | Product ID: {self.product_id}"
