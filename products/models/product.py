from django.db import models

from decimal import Decimal, ROUND_HALF_UP
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

from products.models.brand import Brand
from products.models.subcategory import Subcategory


def get_default_subcategory_id():
    return Subcategory.objects.get(is_default=True).id

def get_default_brand_id():
    return Brand.objects.get(is_default=True).id


class Product(models.Model):
    """
    Represents a product listed in the system.

    Each product is associated with:
        - One category (PCategory)
        - One subcategory (PSubcategory)
        - One brand (PBrand)

    The model stores stock, availability, pricing, discount logic, and the main
    image URL to avoid performing extra JOIN queries during listing operations.

    Default category/subcategory/brand values are handled through helper
    callables because Django requires simple callables for SET_DEFAULT.
    """
    # For future user ratings
    # stars = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    
    # For future products that need these fields like clothing
    # color = models.CharField(max_length=50, null=True, blank=True)
    # size = models.CharField(max_length=50, null=True, blank=True)
    
    # Esto es para exetnder el modelo de producto y reutilizar filters directos en los queryset Products.objects. methods()
    # objects = OptimizedQuerySet.as_manager()
    
    
    # Basic Product Information
    name = models.CharField(
        max_length=120,
        unique=True,
        help_text="Unique display name of the product."
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        null=True,
        help_text="SEO-friendly identifier generated from the product name."
    )
    normalized_name = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        help_text="Lowercased and normalized name used for internal search."
    )

    # Pricing & Availability
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Final selling price."
    )
    price_list = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Price reference for future discount or analytics."
    )
    available = models.BooleanField(
        default=False,
        null=True,
        blank=True,
        help_text="Indicates whether the product is available for purchase."
    )
    stock = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=0,
        help_text="Current available stock."
    )
    stock_reserved = models.PositiveIntegerField(
        default=0,
        help_text="Quantity reserved for pending orders."
    )

    discount = models.IntegerField(
        default=0,
        help_text="Discount percentage applied to the product."
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Detailed product description."
    )

    # Stored to avoid extra DB queries in product listings
    main_image = models.URLField(
        null=True,
        blank=True,
        help_text="URL of the product's main image."
    )

    # Relations FK
    subcategory = models.ForeignKey(
        'Subcategory',
        on_delete=models.SET_DEFAULT,
        default=get_default_subcategory_id,
        help_text="Specific subcategory within its category."
    )
    brand = models.ForeignKey(
        'Brand',
        on_delete=models.SET_DEFAULT,
        default=get_default_brand_id,
        help_text="Brand to which the product belongs."
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the product was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the product was last updated."
    )
    
    # Search vector field for PostgreSQL full-text search
    # ---------------------------------------------------
    # This field stores a precomputed search vector (TSVector) for the product's
    # normalized name. It is used to perform fast full-text searches using
    # PostgreSQL's built-in FTS capabilities.
    #
    # The search_vector is automatically updated via a pre_save signal whenever
    # the normalized_name changes or a new product is created.
    #
    # Benefits:
    # - Allows ranking search results by relevance using SearchRank
    # - Much faster than using multiple LIKE or ILIKE queries for text search
    # - Supports weighted search terms (via weight='A', 'B', etc.)
    search_vector = SearchVectorField(null=True)


    # GIN index on search_vector enables fast full-text searches(FTS)
    
    class Meta:
        indexes = [
            # Standard indexes for filtering / ordering
            models.Index(fields=['price']),       # Fast lookup by price
            # models.Index(fields=['category']),    # Fast filtering by category
            models.Index(fields=['subcategory']), # Fast filtering by subcategory
            models.Index(fields=['brand']),       # Fast filtering by brand
            GinIndex(
                fields=['search_vector'], 
                name='product_search_vector_gin'
            ),
            GinIndex(
                fields=['normalized_name'],
                name='product_normalized_name_gin',
                opclasses=['gin_trgm_ops'] 
            ), 
        ]

    def __str__(self):
        return self.name
    
    def stock_or_available(self, quantity=0) -> tuple:
        """
        Determines whether the product has enough stock and updates its
        availability if needed.

        Args:
            quantity (int, optional):
                Quantity required. Defaults to 0.

        Returns:
            tuple(bool, int):
                - True if there is enough stock, otherwise False.
                - Current stock value.
        """
        stock = self.stock if self.available else 0

        if stock == 0:
            # If stock reaches 0, mark product as unavailable
            if self.available:
                self.available = False
                self.save(update_fields=['available'])
            return False, self.stock

        if stock < quantity:
            return False, self.stock

        return True, self.stock


    def update_main_image(self, url=None):
        """
        Updates the product's stored main image URL.

        Args:
            url (str or None):
                New URL to assign. If None, it clears the main image.
        """
        self.main_image = url
        self.save(update_fields=['main_image'])

        
    def get_all_images_url(self, all_products=False):
        """
        Returns a list of image URLs.

        Args:
            all_products (bool):
                If True, returns all images in the database.
                If False, returns images only for this product.

        Returns:
            list[str]: List of URLs, ordered so main image appears first.
        """
        from products.models.product_image import ProductImage
        
        queryset = ProductImage.objects.all() if all_products else ProductImage.objects.filter(product=self)
        return list(queryset.order_by('-main_image').values_list('image_url', flat=True))

        
    def make_stock_reserved(self, quantity):
        """
        Reserves stock for pending orders.

        Args:
            quantity (int): Quantity to reserve.

        Returns:
            bool: True if reservation was successful, otherwise False.
        """
        print(f'Available {self.available} - Stock: {self.stock} - Quantity: {quantity}')
        if not self.available or self.stock < quantity:
            return False

        self.stock -= quantity
        self.stock_reserved += quantity
        return True
    

    def make_stock_unreserved(self, quantity):
        """
        Releases previously reserved stock.

        Args:
            quantity (int): Quantity to release.
        """
        self.stock += quantity
        self.stock_reserved -= quantity
        self.save()

    
    @property
    def calc_discount(self):
        """
        Used in templates to quickly obtain the discounted price as float.

        Returns:
            float: Price with discount applied using standard rounding.
        """
        return round(float(self.price) * (1 - float(self.discount) / 100), 2)


    def calc_discount_decimal(self):
        """
        Backend-safe version using Decimal for financial accuracy.

        Returns:
            Decimal: Discounted price rounded to 2 decimal places.
        """
        price = Decimal(self.price)
        discount = Decimal(self.discount) / Decimal(100)
        discounted_price = price * (Decimal(1) - discount)
        return discounted_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
