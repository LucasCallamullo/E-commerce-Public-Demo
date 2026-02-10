from typing import Any, Iterable, Optional, Tuple
from collections import defaultdict
from django.db import transaction
from django.db.models import QuerySet

import logging
logger = logging.getLogger(__name__)

from core.utils.utils_db import model_optimized_update
from home.models import StoreImage


class StoreImageService:
    """
    Service layer for managing Store Image retrieval and processing.
    Handles grouping logic for dashboards and public homepages.
    """
    MODEL = StoreImage
    IMAGE_TYPE_BANNER = StoreImage.ImageType.BANNER    # eg: 'banner'
    IMAGE_TYPE_HEADER = StoreImage.ImageType.HEADER
    IMAGE_TYPE_LOGO = StoreImage.ImageType.LOGO
    IMAGE_TYPE_LOGO_WSP = StoreImage.ImageType.LOGO_WSP
    VALUES = ('id', 'image_type', 'image_url', 'main_image', 'available', 'redirect_url')
    
    @classmethod
    def get_dashboard_images(cls, *, store_id: int = 1) -> dict[str, Any]:
        """
        Retrieves store images structured for the administrative dashboard.
        
        Images are categorized by type (header/banner) and further split 
        by their 'available' status (active/inactive).
        
        Returns:
            dict: A dictionary containing the store ID and nested groups of images.
            
        Example response
        ----------------
        {
            "store": { "id": 1 },
            "headers": {
                "active": [...],
                "inactive": [...]
            },
            "banners": {
                "active": [...],
                "inactive": [...]
            }
        }
        """
        # Fetch all images (actives and inactives) for management
        qs_images = cls._get_images_qs_base(
            store_id=store_id, values=cls.VALUES, only_actives=False
        )

        grouped = cls._group_images_by_type(qs_images=qs_images)

        # Ensure stable keys for the frontend even if types are missing in DB
        empty_state = {'active': [], 'inactive': []}
        return {
            'store': {'id': store_id},
            'headers': grouped.get(cls.IMAGE_TYPE_HEADER, empty_state),
            'banners': grouped.get(cls.IMAGE_TYPE_BANNER, empty_state),
            'logos': grouped.get(cls.IMAGE_TYPE_LOGO, empty_state),
            'logos_wsp': grouped.get(cls.IMAGE_TYPE_LOGO_WSP, empty_state),
        }
        
    @classmethod
    def get_home_active_images(cls, *, store_id: int = 1) -> dict[str, list[dict[str, Any]]]:
        """
        Retrieves only active images for the public homepage.
        
        Returns:
            dict: Lists of active images mapped to their types (header, banner).
            
        Example response
        ----------------
        {
            "headers": [...],
            "banners": [...],
        }
        """
        types = (cls.IMAGE_TYPE_BANNER, cls.IMAGE_TYPE_HEADER)
        
        qs_images = cls._get_images_qs_base(
            store_id=store_id, values=cls.VALUES, only_actives=True, types=types
        )
        
        grouped = cls._group_images_by_type(qs_images=qs_images)
        
        return {
            'headers': grouped.get(cls.IMAGE_TYPE_HEADER, {}).get('active', []),
            'banners': grouped.get(cls.IMAGE_TYPE_BANNER, {}).get('active', [])
        }


    @classmethod
    def get_main_by_type(cls, *, store_id: int, image_type: str) -> dict[str, Any] | None:
        """
        Retrieves the primary asset of a specific type for the store.

        This method is designed to fetch 'Big Blobs' of image data (like logos) 
        to be bundled into the store's main cache payload.

        Args:
            - store_id (int): The unique identifier of the store.
            - image_type (str): The category of the image (e.g., 'logo', 'logo_wsp').

        Returns:
            - dict[str, Any]: A dictionary with 'id', 'image_url', and 'redirect_url' 
            if a main image exists; otherwise, None.
        """
        return (
            cls.MODEL.objects
            .filter(store_id=store_id, image_type=image_type, main_image=True)
            .values('id', 'image_url', 'redirect_url')
            .first()
        )

    # ---------------- Serializer Helpers -------------------------------------
    
    @classmethod
    @transaction.atomic
    def handle_delete(cls, *, instance: MODEL, store_id: int | str) -> Optional[MODEL]:
        """
        Orchestrates the deletion of an image and manages the succession logic.
        If the deleted image was 'Main', it promotes the next best candidate.
        """
        is_main = instance.main_image
        image_id = instance.id
        
        # We prepare the QuerySet before deletion
        qs = None
        if is_main:
            qs = cls.get_qs_serializer(
                store_id=store_id, 
                image_type=instance.image_type, 
                exclude_id=image_id
            )
        
        instance.delete()
        logger.info(f"[DELETE]: Image {image_id} removed from DB.")
        
        # 2. Succession Logic: Promote a new main image if necessary
        if qs:
            successor = cls._find_and_promote_successor(qs=qs)
            if successor:
                logger.info(f"[SUCCESSION]: Image {successor.id} promoted after deleting Main image {image_id}.")
                return successor
        
        return None
    
    @classmethod
    @transaction.atomic
    def handle_update(cls, *, qs: QuerySet, instance: MODEL, 
        validated_data: dict) -> Tuple[MODEL, Optional[MODEL]]:
        """
        Handles image updates with side-effect management for 'main_image' status.
        - CASE A: New image becomes Main -> Demote others.
        - CASE B: Main image is demoted -> Find and promote a new successor.
        """
        successor = None
        is_new_main = validated_data.get('main_image', False)
        
        # CASE A: Current image is now MAIN -> Demote everyone else
        if is_new_main:
            # Atomic database update to set previous mains to False
            rows = cls._demote_others_images(qs=qs)
            logger.info(f"[DEMOTION]: {rows} images demoted. Image {instance.id} is now Main.")
            
        # CASE B: Current image was MAIN but now it's NOT -> Promote a successor
        elif not is_new_main and instance.main_image:
            successor = cls._find_and_promote_successor(qs=qs)
            if successor:
                logger.info(f"[PROMOTION]: Image {successor.id} promoted as successor for {instance.id}.")

        # Updates a model instance selectively based on changed values.
        updated = model_optimized_update(instance=instance, validated_data=validated_data)
        
        return updated, successor
    
    @classmethod
    @transaction.atomic
    def handle_create(cls, *, qs: QuerySet, validated_data: dict) -> MODEL:
        """
        Creates a new image while maintaining the single-main-image invariant.
        Automatically promotes the first image of any type to 'Main'.
        """
        # CASE A: Current image is now MAIN -> Demote everyone else
        if validated_data.get('main_image', False):
            # Atomic database update to set previous mains to False
            rows = cls._demote_others_images(qs=qs)
            logger.info(f"[CREATE]: New Main image created. [DEMOTION]: {rows} images demoted.")
        else:
            # Singleton check: Ensure at least one Main image exists per type
            if not qs.filter(main_image=True).exists():
                validated_data['main_image'] = True
                logger.info(f"[CREATE]: No Main found for this type. Setting new image as Main.")

        return cls.MODEL.objects.create(**validated_data)
        
    @staticmethod
    def _find_and_promote_successor(*, qs: QuerySet) -> Optional[MODEL]:
        """
        Business Logic: Finds the best candidate to become the new Main image.
        Prioritizes 'available' images, then orders by oldest (ID).
        We use select_for_update() to lock the row during promotion.
        """
        # We lock the row to prevent other concurrent requests from promoting the same image
        s = qs.filter(main_image=False).select_for_update().order_by('-available', 'id').first()
        if s:
            s.main_image = True
            s.available = True  # Ensure the promoted image is visible
            s.save(update_fields=['main_image', 'available'])
        return s
        
    @staticmethod
    def _demote_others_images(*, qs: QuerySet) -> int:
        """ Performs an atomic demotion of all current Main images in the QuerySet. """
        return qs.filter(main_image=True).update(main_image=False)
    
    @classmethod
    def get_qs_serializer(cls, *, store_id: int, image_type: str, exclude_id: int) -> QuerySet:
        """ Returns a base QuerySet filtered by store and image category. """
        # qs base para casos de post, patch, delete
        qs = cls.MODEL.objects.filter(store_id=store_id, image_type=image_type)
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        return qs
    
    @staticmethod
    def has_other_available_images(*, qs: QuerySet) -> bool:
        """Checks if there are other visible images of the same type."""
        return qs.filter(available=True).exists()
    
    @classmethod
    def get_images_api(cls, *, store_id: int = 1, pk: int = None) -> Optional[dict] | QuerySet:
        """
        Retrieves store images formatted for API consumption.
        Returns a single dict if pk is provided, otherwise returns a ordered QuerySet.
        """
        # 1. Base QuerySet
        qs = cls.MODEL.objects.filter(store_id=store_id)

        if pk:
            return qs.filter(id=pk).values(*cls.VALUES).first()

        # 2. Ordering and Projection
        return qs.order_by('-main_image', 'image_type').values(*cls.VALUES)
        
    # -------------------------------- Private Helpers --------------------------------
    
    @staticmethod
    def _group_images_by_type(qs_images: QuerySet) -> dict[str, dict[str, list[dict]]]:
        """
        Internal processor to group QuerySet results into a nested dictionary.
        
        Images are split into:
        - headers
        - banners

        And each group is further divided into:
        - active   (available = True)
        - inactive (available = False)
        
        ----------------
        Dictionary structure:
        {
          "header":  { "active": [...], "inactive": [...] },
          "banner":  { "active": [...], "inactive": [...] },
          ...
        }
        """
        # defaultdict handles the initialization of nested dictionaries automatically
        grouped = defaultdict(lambda: {'active': [], 'inactive': []})

        # Single pass iteration over the evaluated values QuerySet
        for img in qs_images:
            status = 'active' if img.get('available') else 'inactive'
            image_type = img['image_type']
            grouped[image_type][status].append(img)
        
        return grouped
    
    @classmethod
    def _get_images_qs_base(
        cls, *,
        store_id: int = 1, 
        values: Iterable[str] = None, 
        only_actives: bool = True, 
        types: Iterable[str] = None
    ) -> QuerySet:
        """
        Repository-like method to construct the base StoreImage QuerySet.
        """
        qs = cls.MODEL.objects.filter(store_id=store_id)
        
        if only_actives:
            qs = qs.filter(available=True)
            
        if types:
            qs = qs.filter(image_type__in=types)
        
        # Priority order: Main images first, then by ID
        # qs = qs.order_by('-main_image', 'id')
        qs = qs.order_by('-main_image')
        
        if values:
            return qs.values(*values)
            
        return qs
    