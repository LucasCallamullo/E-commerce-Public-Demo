from typing import Any
from django.db import transaction
from django.db.models import QuerySet, Case, When, Value, BooleanField

# core app
from core.utils.utils_files import delete_physical_files_from_urls

from products.models.product import Product
from products.models.product_image import ProductImage

class ProductImageService:
    """
    Service layer to manage product image retrieval logic.
    Centralizes access to the ProductImage model to ensure consistent 
    filtering and optimized database queries.
    """

    @classmethod
    def get_dashboard_list(cls, *, product_id: int) -> list[dict[str, Any]]:
        """
        Retrieves a list of secondary images for administrative dashboard display.
        
        Returns:
            - List: A list of dictionaries containing 'id', 'image_url', and 'main_image', 
            ordered by priority.
        """
        qs = cls._get_qs_base_images(product_id=product_id)
        return list(qs.values('id', 'image_url', 'main_image').order_by('-main_image'))

    @classmethod
    def get_list_images(cls, *, product_id: int, main_image: bool = None) -> list[ProductImage]:
        """
        Fetch images for a product and cast to list for in-memory operations.
        """
        return list(cls._get_qs_base_images(product_id=product_id, main_image=main_image))
    
    @classmethod
    def get_image_by_id(cls, *, product_id: int, image_id: int | str) -> ProductImage | None:
        qs = cls._get_qs_base_images(product_id=product_id)
        return qs.filter(id=image_id).first()
        
    @staticmethod
    def handle_update_main_image(*, image: ProductImage) -> None:
        """
        It promotes one main image and degrades all others of the same product.
        (All consolidated into a single SQL UPDATE statement)
        
        Logic:
            UPDATE table SET main_image = TRUE WHERE id = target_id
            UPDATE table SET main_image = FALSE WHERE id != target_id AND product_id = X      
        """
        ProductImage.objects.filter(product_id=image.product_id).update(
            main_image=Case(
                When(id=image.id, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        

    @classmethod
    def get_list_urls(cls, product_id: int) -> list[str]:
        """
        Extracts only the image URLs as a flat list of strings.
        Useful for cache invalidation or batch processing.
        
        Args:
            product_id (int): Target product ID.
            get_all (bool): If True, includes the main product image.
            
        Returns:
            list[str]: A list of raw URL strings.
        """
        return list(
            cls
            ._get_qs_base_images(product_id=product_id)
            .order_by('-main_image')
            .values_list('image_url', flat=True)
        )


    @staticmethod
    @transaction.atomic
    def bulk_create_images(product: Product, urls: list[str]) -> dict:
        """
        Business logic for batch image creation and main image management.
        """
        # 1. Check current status
        has_main = ProductImage.objects.filter(product=product, main_image=True).exists()
        
        # 2. Prepare objects list for Bulk Create
        product_image_instances = []
        new_main_assigned = None
        
        for url in urls:
            # If has_main is False, the first image will be True, others False.
            # If has_main is True, all images in this batch will be False.
            product_image_instances.append(
                ProductImage(
                    product=product,
                    image_url=url,
                    main_image=not has_main
                )
            )
            
            # Logic: Set main image only if none exists and update the product reference
            if not has_main:
                # Flip the switch so subsequent images in this loop are marked as False
                has_main = True 
                # method on model Product only updated_fields['main_image']
                product.update_main_image(url=url)
                new_main_assigned = url

        # 5. Execute Bulk Create: Optimizes performance with a single DB query
        if product_image_instances:
            ProductImage.objects.bulk_create(product_image_instances)
  
        return {
            "uploaded_images": urls,
            "total_uploaded": len(urls),
            "main_image_updated": new_main_assigned
        }

    @staticmethod
    @transaction.atomic
    def delete_images_and_update_main(product: Product, image_ids: set) -> dict:
        """
        Deletes a specific set of images from the database and local storage, 
        ensuring the Product's main image is redistributed if necessary.

        Args:
            product (Product): The Product instance associated with the images.
            image_ids (set): A set of validated ProductImage Primary Keys to delete.

        Logic:
            1. Query identifying target images based on product ownership.
            2. Pre-deletion check: Capture image URLs for physical file removal 
            and verify if the primary (main) image is part of the deletion set.
            3. Database deletion: Executes batch delete.
            4. Physical cleanup: Invokes core utility to remove files from disk.
            5. Main image redistribution: If the primary image was removed, 
            the next available image (by ID) is promoted to main.

        Returns:
            dict: {
                "deleted_count": int,
                "main_image_updated": bool,
                "new_main_image": str or None
            }
        """
        # 1. Define the target QuerySet
        images_to_delete_qs = ProductImage.objects.filter(
            id__in=image_ids, 
            product=product
        )
        
        # 2. CAPTURE DATA BEFORE DELETION
        target_data = list(images_to_delete_qs.values('image_url', 'main_image'))
        if not target_data:
            return {"deleted_count": 0, "main_image_updated": False, "new_main_image": None}

        # Extract URLs for local disk cleanup
        image_urls = [img['image_url'] for img in target_data]
        
        # Check if the primary image is being removed before the record is gone
        was_main_deleted = any(img['main_image'] for img in target_data)

        # 3. Database Deletion
        deleted_count, _ = images_to_delete_qs.delete()

        # 4. Physical Storage Cleanup
        # If DB deletion fails, transaction.atomic ensures this step is never reached
        if deleted_count > 0:
            delete_physical_files_from_urls(urls=image_urls)
        
        # 5. Redistribute Main Image Status
        new_main_url = None
        if was_main_deleted and deleted_count > 0:
            # Fetch the next candidate from the remaining images in DB
            new_main_image = (
                ProductImage.objects.filter(product=product)
                .order_by('id')
                .only('id', 'main_image', 'image_url')
                .first()
            )
            # Update the new main_image
            if new_main_image:
                new_main_image.main_image = True
                new_main_image.save(update_fields=['main_image'])
                new_main_url = new_main_image.image_url
            
            # Update the Product's denormalized main_image field
            product.update_main_image(new_main_url)

        return {
            "deleted_count": deleted_count,
            "main_image_updated": was_main_deleted,
            "new_main_image": new_main_url
        }

    
    # ---- Internal Data Access Methods (Repository Logic) ----
    
    @staticmethod
    def _get_qs_base_images(*, product_id: int, main_image: bool = None) -> QuerySet:
        """
        Internal repository method to build the base QuerySet for product images.
        
        Args:
            product_id (int): ID to filter by.
            main_image (bool | None): Filter Images or Not for main_image field.

        Returns:
            QuerySet: Filtered ProductImage objects.
        """
        qs = ProductImage.objects.filter(product_id=product_id)
        
        if main_image is None:
            return qs

        return qs.filter(main_image=main_image)

