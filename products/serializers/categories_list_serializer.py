from rest_framework import serializers

class CleanNullFieldsSerializer(serializers.Serializer):
    """
    Base serializer that optionally removes fields with null-like values.
    
    Behavior:
    ----------
    - Fields with values None, empty string '', or empty list [] are removed from the output.
    - Controlled by the 'clean_nulls' flag in the serializer context (default: True).
    - If 'clean_nulls' is set to False, all fields are included regardless of their values.
    """
    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Check if cleaning is enabled in the context (default True)
        if not self.context.get('clean_nulls', True):
            return data

        return {k: v for k, v in data.items() if v not in (None, '', [])}


class BrandListSerializer(CleanNullFieldsSerializer):
    """
    Serializer for listing brands with optional null field removal.
    
    {
        "id": 3,
        "slug": "sony",
        "name": "Sony",
        "image_url": "https://example.com/images/sony.jpg",
        "is_default": false
    }
    """ 
    id = serializers.IntegerField()
    slug = serializers.CharField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_null=True)
    image_url = serializers.URLField(required=False, allow_null=True)
    is_default = serializers.BooleanField(required=False)


class CategoryListSerializer(CleanNullFieldsSerializer):
    """
    Serializer for listing categories with optional null field removal.
    
    {
        "id": 1,
        "slug": "electronics",
        "name": "Electronics",
        "image_url": null,
        "is_default": true
    }
    """
    id = serializers.IntegerField()
    slug = serializers.CharField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_null=True)
    image_url = serializers.URLField(required=False, allow_null=True)
    is_default = serializers.BooleanField(required=False)


class SubcategoryListSerializer(CleanNullFieldsSerializer):
    """
    Serializer for listing subcategories with optional null field removal.
    
    {
        "id": 5,
        "slug": "headphones",
        "name": "Headphones",
        "image_url": "https://example.com/images/headphones.jpg",
        "is_default": false
    }
    """
    id = serializers.IntegerField()
    slug = serializers.CharField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_null=True)
    image_url = serializers.URLField(required=False, allow_null=True)
    is_default = serializers.BooleanField(required=False)

