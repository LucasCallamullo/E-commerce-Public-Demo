

from django.db import models
from django.conf import settings

from products.models import Product

class FavoriteProduct(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
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
