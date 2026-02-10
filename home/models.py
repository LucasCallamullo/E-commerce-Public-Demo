from django.db import models
import logging
logger = logging.getLogger(__name__)


class Store(models.Model):
    """
    Represents the identity and global configuration of the store.
    
    This model centralizes contact information, tax data, and banking 
    configurations. Since this is a single-store application, it is 
    recommended to access this data via a Cache-enabled Context Processor 
    to optimize performance.
    """
    # --- Basic Information ---
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, max_length=700)
    schedules = models.TextField(blank=True, max_length=250)
    
    # --- Contact Information ---
    # Note: WhatsApp number should include the country code (e.g., 549351...)
    # for correct URL construction in the frontend.
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=180, blank=True, null=True)
    cellphone = models.CharField(max_length=20, blank=True, null=True)
    wsp_number = models.CharField(max_length=20, blank=True, null=True)
    
    # --- Financial Configuration ---
    # "Official or internal exchange rate for USD to ARS conversions."
    usd_exchange_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default='1000.00')
    
    # "Last time the exchange rate was updated."
    usd_last_update = models.DateTimeField(auto_now=True)
    
    # --- Administrative and Banking Data ---
    # These fields are used for billing information and user transfer details.
    """ 
    BANCO GALICIA
    Alias: EMPRESA.GALICIA.CBA
    CBU: 0070148420000008022035
    Cuenta N° 0008022-0 148-3
    Cuit: 30-71750886-2
    Razón Social: EMPRESA GAMES S.A.S.
    """
    # Banco o Billetera (ej: Galicia, Mercado Pago)
    bank_name = models.CharField(max_length=50, blank=True, null=True)
    # Razón Social o Nombre del dueño 
    account_holder = models.CharField(max_length=100, blank=True, null=True)
    # CUIT/CUIL del titular
    cuit = models.CharField(max_length=20, blank=True, null=True)
    # El identificador de 22 dígitos
    cbu_cvu = models.CharField(max_length=22, blank=True, null=True)
    # El nombre corto (ej: TIENDA.GALICIA.CBA)
    alias = models.CharField(max_length=50, blank=True, null=True)
    # Opcional: El número de cuenta formateado (ej: 0008022-0 148-3)
    account_number = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - ID: {self.id}"
    
    
class StoreImage(models.Model):
    """
    Represents image assets associated with a Store.
    
    This model supports different types of display images (headers, banners) 
    and is optimized for high-performance delivery through external storage 
    and database indexing.
    """
    
    class ImageType(models.TextChoices):
        """Enum for categorical classification of store images."""
        HEADER = 'header', 'Header'
        BANNER = 'banner', 'Banner'
        LOGO = 'logo', 'Main Logo'                  # Logo general de la tienda
        LOGO_WSP = 'logo_wsp', 'WhatsApp Logo'      # Logo específico para el botón de WhatsApp
        
        @classmethod
        def home_types(cls) -> tuple[str]:
            return (cls.HEADER, cls.BANNER)
        
    # The store this image belongs to.
    store = models.ForeignKey('Store', related_name='images', on_delete=models.CASCADE)
    
    # Category of the image for UI placement.
    image_type = models.CharField(
        max_length=10, 
        choices=ImageType.choices, 
        default=ImageType.HEADER
    )
    
    redirect_url = models.URLField(max_length=400, blank=True, null=True)
    
    # CharField is used instead of ImageField for architectural design reasons:
    # 1. Decoupling: Separates storage logic from the model. The path is managed 
    #    externally (API/Services), facilitating future migrations to CDNs or Cloud Storage (S3).
    # 2. Performance (Nginx): Enables Nginx to serve files directly as static resources 
    #    via 'alias', bypassing the Django/Python overhead for high-performance delivery.
    # 3. Efficiency: Avoids Django's automatic file-system validations, which can be 
    #    resource-intensive during Bulk Load operations, and simplifies intelligent URL handling.
    # Decoupled: Path managed by API/Service for Nginx/CDN delivery
    image_url = models.CharField(max_length=200, blank=True, null=True)
    
    # This field determines the primary image to be displayed in carousels and product listings.
    main_image = models.BooleanField(default=False)
    available = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.image_type.capitalize()} | Image: {self.id} | Main: {self.main_image}"
    
    def __init__(self, *args, **kwargs):
        """
        Initializes the model and captures the original image_url from the 
        database state without triggering additional SQL queries.
        """
        super().__init__(*args, **kwargs)
        # We access __dict__ directly to avoid triggering deferred field loading.
        # If the 'image_url' field was not included in a .only() or .defer() 
        # query, _original_url will safely be None.
        self._original_url = self.__dict__.get('image_url')

    @property
    def safe_original_url(self) -> str | None:
        """Returns the initial URL without risking a database hit."""
        return self._original_url
    
    @safe_original_url.setter
    def safe_original_url(self, value: str | None):
        """Setter: Manually updates the shadow state of the URL."""
        self._original_url = value

    
    @property
    def needs_cleanup_file(self) -> bool:
        """
        Determines if a previous physical file requires deletion.

        Returns:
            bool: True if a valid original URL exists and it differs from 
                  the current memory state (meaning the file path was updated).
        """
        # 1. Si no hay PK o no tenemos snapshot del original, no hay nada que limpiar
        if not self.pk or not self._original_url:
            logger.debug(
                "[FILE_MIXIN][needs_cleanup_file] not pk: %s or not self._original_url: %s", 
                self.pk, self._original_url
            )
            return False
        
        # 2. Obtenemos el valor actual de memoria SIN disparar SQL
        current_url = self.__dict__.get('image_url')
        if current_url is None:
            logger.debug("[FILE_MIXIN][needs_cleanup_file] current_url is None")
            return False
        
        # 2. self._original_url != self.image_url: Detects a path change.
        changed = bool(self._original_url != current_url)
        logger.debug("[FILE_MIXIN][needs_cleanup_file] bool: %s", changed)
        return changed

    class Meta:
        verbose_name = "Store Image"
        verbose_name_plural = "Store Images"
        # Optimized for fetching available images of a specific type ordered by priority.
        indexes = [
            models.Index(fields=['image_type', 'available', '-main_image']),
        ]

    
class SocialMedia(models.Model):
    """
    Manages social media profiles associated with a Store.
    
    Includes a platform mapping to Remix Icon classes for frontend rendering.
    Enforces a unique platform per store via Meta constraints.
    """
    
    class PlatformEnum(models.TextChoices):
        """Enumeration of supported social media platforms."""
        FB = 'fb', 'Facebook'
        GG = 'gg', 'Google'
        GM = 'gm', 'Google Maps'
        IG = 'ig', 'Instagram'
        TT = 'tt', 'TikTok'
        TW = 'tw', 'X (Twitter)'
        YT = 'yt', 'YouTube'
    
    store = models.ForeignKey('Store', related_name='social_networks', on_delete=models.CASCADE)
    platform = models.CharField(
        max_length=10, 
        choices=PlatformEnum.choices, 
        default=PlatformEnum.IG
    )
    url = models.URLField(blank=True, null=True, default="https://www.instagram.com")
    is_active = models.BooleanField(default=True)
    is_main = models.BooleanField(default=False)

    class Meta:
        unique_together = ('store', 'platform')
        
    def __str__(self):
        return f"{self.get_platform_display()} - {self.store.name}"
        
    @staticmethod
    def get_icon_class(value: str) -> str:
        """
        Returns the specific Remix Icon (ri-) class based on the platform.
        Usage in templates: {{ object.icon_class }}
        """
        icons = {
            'gg': 'ri-google-fill',
            'ig': 'ri-instagram-line',
            'fb': 'ri-facebook-box-fill',
            'tt': 'ri-tiktok-fill',
            # 'tw': 'ri-twitter-line',
            'tw': 'ri-twitter-x-line',
            'yt': 'ri-youtube-fill',
            'gm': 'ri-pin-distance-line',
        }
        # Returns a generic community icon if the platform is not found
        return icons.get(value, 'ri-user-community-line') # Icono por defecto
