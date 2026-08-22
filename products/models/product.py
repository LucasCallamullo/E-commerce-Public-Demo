from django.db import models, IntegrityError

from decimal import Decimal, ROUND_HALF_UP
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

# products app
from products.models.mixins import SlugFieldMixin
import logging
logger = logging.getLogger(__name__)


def get_default_category_id():
    from products.models.category import Category
    default_id = Category.objects.filter(is_default=True).values_list('id', flat=True).first()
    
    if default_id is None:
        m = """Critical Error: Default Category not found.
            Ensure a Category with is_default=True exists in the database."""
        logger.error("%s", m)
        raise IntegrityError(m)
    
    return default_id


def get_default_brand_id():
    from products.models.brand import Brand
    default_id = Brand.objects.filter(is_default=True).values_list('id', flat=True).first()
    
    if default_id is None:
        m = """Critical Error: Default Brand not found.
            Ensure a Brand with is_default=True exists in the database."""
        logger.error("%s", m)
        raise IntegrityError(m)
    
    return default_id


class Product(SlugFieldMixin, models.Model):
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
    # para actualizar normalized_name en SlugFieldMixin
    HAS_NORMALIZED_NAME = True
    
    # --------------------------------------- Basic Product Information
    # "Unique display name of the product."
    name = models.CharField(max_length=120, unique=True)
    # "SEO-friendly identifier generated from the product name."
    slug = models.SlugField(max_length=120, unique=True, blank=True, null=True)
    # "Lowercased and normalized name used for internal search."
    normalized_name = models.CharField(max_length=120, blank=True, null=True)
    # "Stock Keeping Unit - Unique identifier for inventory management."
    sku = models.CharField(max_length=50, blank=True, null=True)

    # --------------------------------------- Pricing   (Bimonetary)
    # "Indicates if ARS and USD prices are synchronized based on exchange rate."
    is_linked_prices = models.BooleanField(default=False)

    # "Final selling price."
    price_ars = models.DecimalField(max_digits=12, decimal_places=2, default="0.00")
    # "Costo promedio de adquisición (WAC) para cálculo de márgenes."
    cost_avg_ars = models.DecimalField(max_digits=12, decimal_places=2, default="0.00")
    # "Discount percentage applied to the product."
    discount_ars = models.IntegerField(default=0)
    
    # "Final selling price in US Dollars."
    price_usd = models.DecimalField(max_digits=12, decimal_places=2, default="0.00")
    # "Discount percentage applied to USD price."
    discount_usd = models.IntegerField(default=0)
    
    # ------------------------------------------  Availability & Details
    # "Price reference for future discount or analytics."
    price_list = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    # "Indicates whether the product is available for purchase."
    available = models.BooleanField(default=False, null=True,  blank=True)
    # "Current available stock."
    stock = models.PositiveIntegerField(null=True, blank=True, default=0)
    # "Quantity reserved for pending orders."
    stock_reserved = models.PositiveIntegerField(default=0)
    # "Detailed product description."
    description = models.TextField(null=True, blank=True)

    # --------------------------------------- Stored to avoid extra DB queries in product listings
    #
    # CharField is used instead of ImageField for architectural design reasons:
    # 1. Decoupling: Separates storage logic from the model. The path is managed 
    #    externally (API/Services), facilitating future migrations to CDNs or Cloud Storage (S3).
    # 2. Performance (Nginx): Enables Nginx to serve files directly as static resources 
    #    via 'alias', bypassing the Django/Python overhead for high-performance delivery.
    # 3. Efficiency: Avoids Django's automatic file-system validations, which can be 
    #    resource-intensive during Bulk Load operations, and simplifies intelligent URL handling.
    # "URL of the main image product."
    main_image = models.CharField(max_length=200, blank=True, null=True)

    # --------------------------------------- Relations FK
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_DEFAULT,
        default=get_default_category_id
    )
    subcategory = models.ForeignKey(
        'Subcategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True, 
        default=None
    )
    brand = models.ForeignKey(
        'Brand', 
        on_delete=models.SET_DEFAULT, 
        default=get_default_brand_id
    )
    
    # --------------------------------------- Metadata
    # "Timestamp when the product was created."
    created_at = models.DateTimeField(auto_now_add=True)
    # "Timestamp when the product was last updated."
    updated_at = models.DateTimeField(auto_now=True)
    
    # Search vector field for PostgreSQL full-text search
    # ---------------------------------------------------
    search_vector = SearchVectorField(null=True)
    
    # For future user ratings
    # stars = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    
    # For future products that need these fields like clothing
    # color = models.CharField(max_length=50, null=True, blank=True)
    # size = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        # FK indexan automatico sería redundante redeclarar en Meta.
        # models.Index(fields=['category']),    # Fast filtering by category
        # models.Index(fields=['subcategory']), # Fast filtering by subcategory
        # models.Index(fields=['brand']),       # Fast filtering by brand
        indexes = [
            # Indice creado para velocidad en filter comunes y cubre: 
            # -    .filter(available=...)
            # -    .filter(available=..., category=...)
            # -    .filter(available=..., category=..., subcategory=...)
            models.Index(fields=['available', 'category', 'subcategory'], name='product_nav_filter_idx'),
            
            # Standard indexes for optimized ordering .order_by('price', 'id')
            models.Index(fields=['price_ars', 'id'], name='product_price_id_idx'),
            
            # GIN: Búsqueda de Texto Completo (FTS) Full Text Search
            # FTS -> Búsqueda semántica por lexemas (raíces de palabras).
            # Ignora "stop words" (de, la, el) y permite buscar por relevancia (Rank).
            # extremadamente rápido para volúmenes grandes de texto.
            GinIndex(
                fields=['search_vector'], 
                name='product_search_vector_gin'
            ),
            
            # 4. GIN TRIGRAM: Búsqueda difusa (Fuzzy Search / typos).
            # Permite encontrar resultados incluso con errores ortográficos (typos).
            # Compara fragmentos de 3 letras para calcular similitud.
            # REQUERIMIENTO: Tener la extensión 'pg_trgm' activada en Postgres.
            GinIndex(
                fields=['normalized_name'],
                name='product_normalized_name_gin',
                opclasses=['gin_trgm_ops'] 
            ), 
        ]
        
    def __str__(self):
        return f'Product: {self.id} | {self.name}'
    
    def __init__(self, *args, **kwargs):
        """
        Initializes the model instance and captures the initial relational state.
        
        A 'snapshot' of category and subcategory IDs is stored in memory. This allows
        us to detect changes during the save() lifecycle without triggering 
        additional SQL queries to compare against the database state.
        """
        super().__init__(*args, **kwargs)
        
        # Internal snapshots of relational IDs to optimize change detection.
        # Direct __dict__ access prevents triggering Deferred attribute loading.
        self._subcategory_id = self.__dict__.get('subcategory_id')
        self._category_id = self.__dict__.get('category_id')

    def has_changes_on_categories(self) -> bool:
        """
        Determines if the relational integrity needs to be validated.
        
        Returns True if:
            1. The instance is being created (new record).
            2. The category_id or subcategory_id has changed from its original state.
        
        Returns False if:
            1. 'skip_integrity_check' is set (e.g., via Serializer validation).
            2. No relational changes are detected in an existing instance.
        """
        # Bypass mechanism for performance optimization when data is pre-validated (e.g., DRF)
        if getattr(self, 'skip_integrity_check', False):
            return False
        
        # Retrieve current memory values (fast access)
        current_sub_id = self.__dict__.get('subcategory_id')
        current_cat_id = self.__dict__.get('category_id')
        
        # Detect modifications in existing relationships
        if current_cat_id and current_sub_id:
            # Check if either ID deviates from the snapshot captured in __init__
            if current_cat_id != self._category_id:
                return True
            if current_sub_id != self._subcategory_id:
                return True
            
        # New instances (without a Primary Key) always require an integrity check
        # unless explicitly bypassed via the 'skip_integrity_check' attribute.
        if not self.pk:
            return True
            
        return False

    def has_category_consistency(self):
        """
        Validates the hierarchical relationship between Category and Subcategory.
        
        This method acts as a secondary safety net (a "bunker") to ensure that the 
        assigned Subcategory actually belongs to the selected Category. 
        
        It only executes if changes are detected in the relational fields, 
        optimizing performance for standard updates.
        
        Raises:
            IntegrityError: If a mismatch is found between Category and Subcategory.
        """
        if self.has_changes_on_categories():
            # Retrieve current IDs from memory to avoid unnecessary database lookups.
            current_sub_id = self.__dict__.get('subcategory_id')
            current_cat_id = self.__dict__.get('category_id')
            
            # Perform cross-reference validation.
            # Note: Accessing self.subcategory may trigger a query if not prefetched, 
            # but this is acceptable here as a critical integrity safeguard.
            if current_sub_id and self.subcategory.category_id != current_cat_id:
                msg = f"""Integrity Conflict: Subcategory {current_sub_id} 
                    is not a child of Category {current_cat_id}."""
                logger.error(msg)
                
                # We raise an IntegrityError because this state indicates a logic 
                # failure in the persistence layer or a potential security bypass.
                raise IntegrityError(msg)
        
    def save(self, *args, **kwargs):
        """
        Custom save pipeline that enforces business rules and maintains state snapshots.
        
        Workflow:
            1. Validate hierarchical consistency before touching the database.
            2. Execute standard persistence via super().save().
            3. Synchronize internal snapshots to reflect the new database state.
        """
        # Step 1: Pre-save integrity audit.
        self.has_category_consistency()
        
        # Step 2: Database persistence.
        saved = super().save(*args, **kwargs)
        
        # Step 3: Post-persistence state synchronization.
        # We update the 'original' snapshots so that subsequent saves within 
        # the same execution context correctly identify new changes.
        self._category_id = self.category_id
        self._subcategory_id = self.subcategory_id
        
        return saved


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


    def update_main_image(self, url: str | None = None) -> str | None:
        """
        Updates the product's stored main image URL.
        """
        if self.main_image != url:
            self.main_image = url
            self.save(update_fields=['main_image'])
        return url

        
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
        return round(float(self.price_ars) * (1 - float(self.discount_ars) / 100), 2)


    def calc_discount_decimal(self):
        """
        Backend-safe version using Decimal for financial accuracy.

        Returns:
            Decimal: Discounted price rounded to 2 decimal places.
        """
        price = Decimal(self.price_ars)
        discount = Decimal(self.discount_ars) / Decimal(100)
        discounted_price = price * (Decimal(1) - discount)
        return discounted_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
