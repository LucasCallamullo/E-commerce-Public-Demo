from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'

    # Asegura que las señales se carguen
    def ready(self):
        import payments.signals  