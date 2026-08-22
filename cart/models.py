from django.db import models

# Create your models here.
# from products.models.product import Product



from django.db import models

class Cart(models.Model):
    """
    Represents a shopping cart associated with a single user.

    Fields:
        user (CustomUser): One-to-one relationship to the user who owns this cart.
        last_modified (datetime): Auto-updated timestamp of the last cart modification.
    """
    user = models.OneToOneField(
        'users.CustomUser', 
        on_delete=models.CASCADE, 
        related_name="carrito"
    )
    # auto_now: Django updates this field automatically on every save
    last_modified = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['last_modified']),  # Optional, redundant with db_index=True
        ]


class CartItem(models.Model):
    """
    Represents a product entry in a user's cart.

    Fields:
        cart (Cart): ForeignKey linking to the Cart this item belongs to.
        product (Product): ForeignKey linking to the product.
        quantity (int): Number of units of the product in the cart.
    """
    cart = models.ForeignKey(
        'Cart', 
        on_delete=models.CASCADE, 
        related_name="items"
    )
    product = models.ForeignKey(
        "products.Product", 
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        indexes = [
            models.Index(fields=['cart', 'product']),  # Optimizes queries filtering by cart and product
        ]

