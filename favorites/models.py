

from django.db import models
from django.conf import settings


class FavoriteProduct(models.Model):
    """
    Model representing a user's favorite product.

    Each user can mark multiple products as favorites, but a user cannot
    favorite the same product more than once.

    Constraints:
        - UniqueConstraint ensures a user cannot favorite the same product twice.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    
    # product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE)
    
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_favorite')
        ]

        # maybe useful in the future
        # unique_together = ('user', 'product')
        # indexes = [models.Index(fields=['user']), models.Index(fields=['product']),]
        
    def __str__(self):
        return f"{self.user.username} -- {self.product.name}"
