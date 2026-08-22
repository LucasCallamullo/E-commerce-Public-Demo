from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'
    
    def ready(self):
        import products.signals.defaults
        import products.signals.storage_signals
        import products.signals.cache_signals
        import products.signals.category_signals
