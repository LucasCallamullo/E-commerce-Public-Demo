

from django.db import models
from django.db.models import Q
from django.utils.text import slugify

class ProtectDefaultMixin:
    """
        Mixin que evita modificar o eliminar objetos marcados como `is_default=True`.
        También actualiza automáticamente el slug si cambia el nombre.
        
        Este mixin asume que el modelo tiene los atributos:
        - name (str)
        - slug (str)
        - is_default (bool)
        
        Protege instancias por defecto contra edición o eliminación.
    """
    protected_message = "No se puede modificar o eliminar una instancia por defecto."
    
    def save(self, *args, **kwargs):
        # to save the first time slug, after on this we save manually when changes the name
        if not self.pk:
            if self.name:
                self.slug = slugify(self.name)
        
        # Evitar modificar instancias por default
        if self.pk and getattr(self, 'is_default', False):
            raise ValueError(self.protected_message)
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if getattr(self, 'is_default', False):
            raise ValueError(self.protected_message)
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name or "Unnamed model"
    

# El orden de herencia importa: poné ProtectDefaultMixin primero, antes de models.Model, 
# para que su método save y delete tengan prioridad.
class PCategory(ProtectDefaultMixin, models.Model):
    protected_message = "No se puede modificar o eliminar la categoría por defecto."
    
    name = models.CharField(max_length=32, unique=True)
    slug = models.SlugField(max_length=32, unique=True, null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
        
    @classmethod
    def get_default_model_or_id(cls, model=False):
        """ Metodo para crear u obtener la marca default y retorna el id de la misma para seteos default"""
        category, _ = cls.objects.get_or_create(
            name="Sin Categoría",
            slug="sin-categoria",
            defaults={'is_default': True}
        )
    
        return category if model else category.id

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['slug'],
                name='pcategory_unique_slug',
                condition=Q(slug__isnull=False)  # Usa Q directamente
            )
        ]
        indexes = [
            models.Index(
                fields=['slug'],
                name='pcategory_slug_idx',
                condition=Q(slug__isnull=False)  # Usa Q directamente
            )
        ]

class PSubcategory(ProtectDefaultMixin, models.Model):
    protected_message = "No se puede modificar o eliminar la sub-categoría por defecto."
    
    name = models.CharField(max_length=32)  # Removed unique=True
    slug = models.SlugField(max_length=32, null=True, blank=True)  # Removed unique=True
    image_url = models.URLField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    category = models.ForeignKey('PCategory', on_delete=models.CASCADE, related_name='subcategories')
        
    @classmethod
    def get_default_model_or_id(cls, model=False):
        """Obtener o crear subcategoría default con una categoría default"""
        default_category = PCategory.get_default_model_or_id(model=True)
        
        subcategory, _ = cls.objects.get_or_create(
            name="Sin Subcategoría",
            category=default_category,
            defaults={
                'slug': "sin-subcategoria",
                'is_default': True
            }
        )
        
        return subcategory if model else subcategory.id

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'category'],
                name='psubcategory_unique_name_per_category'
            ),
            models.UniqueConstraint(
                fields=['slug'],
                name='psubcategory_unique_non_null_slug',
                condition=models.Q(slug__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['category'],
                condition=models.Q(is_default=True),
                name='psubcategory_unique_default_per_category'
            )
        ]
        indexes = [
            models.Index(
                fields=['slug'],
                name='psubcategory_slug_idx',
                condition=models.Q(slug__isnull=False),
            ),
            models.Index(
                fields=['category', 'name'],
                name='psubcategory_category_name_idx'
            )
        ]
        verbose_name = 'Subcategoría de Producto'
        verbose_name_plural = 'Subcategorías de Productos'


class PBrand(ProtectDefaultMixin, models.Model):
    protected_message = "No se puede modificar o eliminar la marca por defecto."
    
    name = models.CharField(max_length=32, unique=True)
    slug = models.SlugField(max_length=32, unique=True, null=True, blank=True)  # Slug único (opcional)
    image_url = models.URLField(null=True, blank=True)
    is_default = models.BooleanField(default=False)        # Para identificar la categoría especial
        
    @classmethod
    def get_default_model_or_id(cls, model=False):
        """ Metodo para crear u obtener la marca default y retorna el id de la misma para seteos default"""
        brand, _ = cls.objects.get_or_create(
            name="Sin Marca",
            slug="sin-marca",
            defaults={'is_default': True}
        )
        
        return brand if model else brand.id
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['slug'],
                name='pbrand_unique_slug',
                condition=Q(slug__isnull=False)  # Usa Q directamente
            )
        ]
        indexes = [
            models.Index(
                fields=['slug'],
                name='pbrand_slug_idx',
                condition=Q(slug__isnull=False)  # Usa Q directamente
            )
        ]
    

class ProductImage(models.Model):
    """
    Represents an image associated with a product.
    Multiple images can be linked to the same product,
    but only one is marked as the main image.
    """
    product = models.ForeignKey(
        'Product', on_delete=models.CASCADE, related_name='images', 
        help_text="The product this image belongs to."
    )
    image_url = models.URLField(null=True, blank=True, help_text="URL of the image.")
    main_image = models.BooleanField(default=False, help_text="Main image of a product.")
    
    def update_main_image(self, images_list=None):
        """ 
        Marks this image as the main image and updates the rest as not main.
        
        Args:
            queryset (QuerySet[ProductImage], optional): Prefetched queryset of images belonging 
            to the same product. If provided, it avoids extra DB queries when unsetting other 
            main images.
        """
        if images_list is not None:
            other_ids = [img.id for img in images_list if img.id != self.id]
            if other_ids:
                ProductImage.objects.filter(id__in=other_ids).update(main_image=False)

        self.main_image = True
        self.save(update_fields=['main_image'])
        
        
    def delete(self, *args, **kwargs):
        """
        Overrides the default delete method to:
        - Assign a new main image from the remaining ones if this was the main.
        - Update the product's main_image_url field accordingly.
        """
        is_main = self.main_image
        product = self.product if is_main else None
        super().delete(*args, **kwargs)   

        if product:
            new_main = product.images.first()
            if new_main:
                new_main.update_main_image()
                product.update_main_image(new_main.image_url)
            
    def __str__(self):
        return f"Url: {self.image_url} | Product ID: {self.product_id}"
    

# Se debe llamar a  funciones anonimas de esta forma para lograr lo que queremos 
# de setear un valor por defecto on_delete o on_create 
def get_default_category():
    return PCategory.get_default_model_or_id()

def get_default_subcategory():
    return PSubcategory.get_default_model_or_id()

def get_default_brand():
    return PBrand.get_default_model_or_id()
    
from decimal import Decimal, ROUND_HALF_UP
class Product(models.Model):
    # For future user ratings
    # stars = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    
    # For future products that need these fields like clothing
    # color = models.CharField(max_length=50, null=True, blank=True)
    # size = models.CharField(max_length=50, null=True, blank=True)
    
    # Esto es para exetnder el modelo de producto y reutilizar filters directos en los queryset Products.objects. methods()
    # objects = OptimizedQuerySet.as_manager()

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True, null=True)
    normalized_name = models.CharField(max_length=120, blank=True, null=True)
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_list = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    available = models.BooleanField(default=False, null=True, blank=True)
    stock = models.PositiveIntegerField(null=True, blank=True, default=0)
    stock_reserved = models.PositiveIntegerField(default=0)
    
    discount = models.IntegerField(default=0)
    description = models.TextField(null=True, blank=True)
    main_image = models.URLField(null=True, blank=True)    # asociar una url main, para evitar consultas
    
    # One-to-one relationship, each product has a category, subcategory, and brand
    # ejempl definicion de modelo default base con metodo en cada clase
    category = models.ForeignKey('PCategory', on_delete=models.SET_DEFAULT, default=get_default_category)
    subcategory = models.ForeignKey('PSubcategory', on_delete=models.SET_DEFAULT, default=get_default_subcategory)
    brand = models.ForeignKey('PBrand', on_delete=models.SET_DEFAULT, default=get_default_brand)

    # Date fields for product price updates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['price']),
            ##
            models.Index(fields=['category']),
            models.Index(fields=['subcategory']),
            models.Index(fields=['brand']),
        ]
    
    def __str__(self):
            return self.name
        
    def stock_or_available(self, quantity=0) -> tuple:
        """
        Checks if the product has sufficient stock and updates its availability status if necessary.

        Args:
            quantity (int, optional): The amount of stock required. Defaults to 0.

        Returns:
            bool: True if there is enough stock to fulfill the quantity, False otherwise.
            int: Stock of the product.
        """
        # If the product is available, use its stock; otherwise, assume zero stock.
        stock = self.stock if self.available else 0

        # If there is no stock, mark the product as unavailable (logical deletion)
        if stock == 0:
            if self.available:
                self.available = False
                self.save(update_fields=['available'])
            return False, self.stock

        # If the stock is insufficient for the requested quantity
        if stock < quantity:
            return False, self.stock

        # If none of the above conditions were met, there is enough stock
        return True, self.stock

    def update_main_image(self, url= None):
        """ Method for update main_image field with the new url, 
        or None in some case, if deleted all images of one product. """
        self.main_image = url
        self.save(update_fields=['main_image'])
        
    def get_all_images_url(self, all_products=False):
        queryset = ProductImage.objects.all() if all_products else ProductImage.objects.filter(product=self)
        return list(queryset.order_by('-main_image').values_list('image_url', flat=True))
        
    def make_stock_reserved(self, quantity):
        """ Method for products to reserve stock for different payment orders """
        print(f'Available {self.available} - Stock: {self.stock} - Cantidad: {quantity}')
        if not self.available or self.stock < quantity:
            return False
        
        print('reservo el stock')
        self.stock -= quantity
        self.stock_reserved += quantity
        return True
    
    def make_stock_unreserved(self, quantity):
        self.stock += quantity
        self.stock_reserved -= quantity
        self.save()
    
    @property
    def calc_discount(self):
        """For templates - returns float rounded to 2 decimals."""
        return round(float(self.price) * (1 - float(self.discount) / 100), 2)

    def calc_discount_decimal(self):
        """For internal logic - returns Decimal rounded to 2 decimals."""
        price = Decimal(self.price)
        discount = Decimal(self.discount) / Decimal(100)
        discounted_price = price * (Decimal(1) - discount)
        return discounted_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    
    
