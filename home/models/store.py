from django.db import models


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
    