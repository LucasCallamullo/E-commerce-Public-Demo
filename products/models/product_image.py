from django.db import models


class ProductImage(models.Model):
    """
    Represents an image linked to a product.

    A product may have multiple images, but exactly one can be designated
    as the main image. This model manages individual image records as well
    as helper logic that automatically updates the main image selection.
    """
    # "The product this image belongs to."
    product = models.ForeignKey(
        'Product', 
        on_delete=models.CASCADE, 
        related_name='images',
        # Desactivo el index por defecto que crea django en mi fk por mi index en Meta
        db_index=False    
    )
    
    # CharField is used instead of ImageField for architectural design reasons:
    # 1. Decoupling: Separates storage logic from the model. The path is managed 
    #    externally (API/Services), facilitating future migrations to CDNs or Cloud Storage (S3).
    # 2. Performance (Nginx): Enables Nginx to serve files directly as static resources 
    #    via 'alias', bypassing the Django/Python overhead for high-performance delivery.
    # 3. Efficiency: Avoids Django's automatic file-system validations, which can be 
    #    resource-intensive during Bulk Load operations, and simplifies intelligent URL handling.
    image_url = models.CharField(max_length=200, blank=True, null=True) # "URL of the image."
    
    # "Indicates whether this is the product's main image."
    main_image = models.BooleanField(default=False)


    class Meta:
        indexes = [
            # Indice creado para velocidad en filter comunes, orders_by y cubre: 
            # -    .filter(product_id=...)
            # -    .filter(product_id=..., main_image=...)
            models.Index(fields=['product', '-main_image']),
        ]

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
        return f"Image Url: {self.image_url} | Product ID: {self.product_id}"
