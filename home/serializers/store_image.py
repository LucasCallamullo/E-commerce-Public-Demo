from rest_framework import serializers

# core app
from core.utils.utils_parsers import parse_bool, parse_url

from home.models import StoreImage
from home.services.store_image import StoreImageService

class StoreImageSerializer(serializers.ModelSerializer):
    """
    Serializer for StoreImage model.
    Handles business logic for unique main images per type and ensures 
    at least one available image remains per category.
    
    """
    image_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    # Overriding to bypass automatic ChoiceField validation for custom messaging
    image_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    # Overriding to bypass automatic URLField validation for custom messaging
    redirect_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    class Meta:
        model = StoreImage
        fields = ['id', 'image_type', 'redirect_url', 'image_url', 'main_image', 'available']
        extra_kwargs = {
            'id': {'read_only': True},
            'main_image': {'required': False},
            'available': {'required': False},
        }
        
    def validate_redirect_url(self, value) -> str | None:
        return parse_url(value=value, field_name="URL Redirección")

    def validate_image_type(self, value) -> str:
        """Ensures the image_type exists within defined TextChoices."""
        if value not in StoreImage.ImageType.values:
            raise serializers.ValidationError('Image type not defined.')
        return value
    
    def validate_main_image(self, value) -> bool:
        return parse_bool(value, field_name='Main Imagen.')
    
    def validate_available(self, value) -> bool:
        return parse_bool(value, field_name='Imagen Disponible.')
    
    def validate_image_url(self, value) -> str | None:
        """Preserves existing URL if no new value is provided during updates."""
        if not value and self.instance:
            return self.instance.image_url
        return value
    
    def validate(self, attrs) -> dict:
        """
        Cross-field validation:
        1. Ensures consistency between 'main_image' and 'available' status.
        2. Prevents a store from having zero available images of a specific type.
        3. Prepares the QuerySet for demoting other main images.
        """
        # 1. Safely retrieve values from input or instance (for PATCH support)
        image_type = attrs.get('image_type', self.instance.image_type if self.instance else None)
        if not image_type:
            raise serializers.ValidationError({"image_type": "Image type not defined."})
        
        is_new_main = attrs.get('main_image', self.instance.main_image if self.instance else False)
        is_available = attrs.get('available', self.instance.available if self.instance else True)

        # 2. Business Logic: Visibility consistency
        if is_new_main and not is_available:
            raise serializers.ValidationError({
                "main_image": "No se puede marcar como Imagen Principal si está oculta."
            })
        
        # 3. Singleton validation per Store/Type
        qs = StoreImageService.get_qs_serializer(
            store_id=self.context.get("store").get('id'),
            image_type=image_type,
            exclude_id=self.instance.id if self.instance else 0
        )
        
        # Attach QuerySet of conflicting main images to validated_data for post-save demotion
        attrs['_qs_context'] = qs
        
        # Rule: Prevent hiding the last available image for this type
        if not is_available and not StoreImageService.has_other_available_images(qs=qs):
            raise serializers.ValidationError({
                "available": "No se puede ocultar la única imagen activa."
            })
            
        return attrs
    
    
    def create(self, validated_data) -> StoreImage:
        """
        Overrides create to demote previous main images.
        """
        # Extract the demotion QuerySet prepared in validate()
        qs_context = validated_data.pop('_qs_context', StoreImage.objects.none())
        # Ensure store_id from View context is assigned to the new instance
        validated_data['store_id'] = self.context.get('store').get('id')
        return StoreImageService.handle_create(qs=qs_context, validated_data=validated_data)
    
    
    def update(self, instance, validated_data) -> StoreImage:
        """
        Overrides update to demote previous main images atomically.
        """
        # Extract the demotion QuerySet prepared in validate()
        qs_context = validated_data.pop('_qs_context', StoreImage.objects.none())
        
        updated, successor = StoreImageService.handle_update(
            qs=qs_context, instance=instance, validated_data=validated_data
        )
        # Este atributo es recuperado en to_representation para enviar info_extra
        if successor:
            updated._side_effects = {
                "id": successor.id,
                "main_image": successor.main_image,
                "available": successor.available,
                "image_type": successor.image_type
            }
        return updated
    
    
    def to_representation(self, instance) -> dict:
        """
        Extends the default representation to include transactional side effects.
        """
        # 1. Generate the standard JSON (base model fields)
        representation = super().to_representation(instance)
        
        # 2. Retrieve the transient '_side_effects' attribute injected during the logic flow.
        # This attribute is volatile and exists only for the duration of the current request.
        side_effects = getattr(instance, '_side_effects', None)
        if side_effects:
            representation['meta_updates'] = side_effects
            
        return representation
