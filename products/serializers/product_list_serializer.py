from rest_framework import serializers

class ProductListSerializer(serializers.Serializer):
    """
    Serializer for listing products in a compact format for API responses.
    
    Fields:
    ----------
    id : int
        Unique identifier of the product.
    slug : str | None
        URL-friendly version of the product name, optional.
    name : str
        Name of the product.
    price : Decimal
        Current price of the product.
    price_list : Decimal | None
        Original or list price of the product, optional.
    available : bool | None
        Indicates if the product is available for purchase.
    stock : int
        Quantity of items in stock.
    discount : int
        Discount percentage applied to the product.
    updated_at : datetime | None
        Last update timestamp, optional.
    main_image : str | None
        URL of the main product image, optional.
    is_favorited : bool
        Indicates whether the product is in the user's favorites.
    brand_id : int
        ID of the brand associated with the product.
    category_id : int
        ID of the category associated with the product.
    subcategory_id : int
        ID of the subcategory associated with the product.

    Notes:
    ------
    - The `to_representation` method ensures `price_list` is always included, even if null.
    - `is_favorited` is calculated using the `favorites_ids` passed in the serializer context.
    
    Example:
    --------
    {
        "id": 12,
        "slug": "wireless-headphones",
        "name": "Wireless Headphones",
        "price": "79.99",
        "price_list": "99.99",
        "available": true,
        "stock": 25,
        "discount": 20,
        "updated_at": "2025-11-28T14:12:05Z",
        "main_image": "https://example.com/images/wireless-headphones.jpg",
        "is_favorited": true,
        "brand_id": 3,
        "category_id": 1,
        "subcategory_id": 5
    }
    """
    id = serializers.IntegerField()
    slug = serializers.CharField(required=False, allow_null=True)
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_list = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    available = serializers.BooleanField(required=False, allow_null=True)
    stock = serializers.IntegerField()
    discount = serializers.IntegerField()
    updated_at = serializers.DateTimeField(required=False, allow_null=True)
    main_image = serializers.CharField(required=False, allow_null=True)
    
    # Boolean to indicate if the product is favorited by the current user
    is_favorited = serializers.SerializerMethodField()
    
    # Only IDs are returned to reduce payload size
    brand_id = serializers.IntegerField()
    category_id = serializers.IntegerField()
    subcategory_id = serializers.IntegerField()
    
    def to_representation(self, instance):
        """
        Customize the representation to filter out null values,
        but always include 'price_list' even if it is null.
        """
        rep = super().to_representation(instance)
        allowed_nulls = {'price_list'}
        return {k: v for k, v in rep.items() if v is not None or k in allowed_nulls}

    def get_is_favorited(self, obj):
        """
        Determine if the product is in the user's favorites.
        
        Returns:
        --------
        bool
            True if the product ID is in the favorites list; False otherwise.
        """
        favorites_ids = self.context.get('favorites_ids', None)
        if not favorites_ids:
            return False
        return obj['id'] in favorites_ids

    
