

# Create your models here.
from django.db import models


class StatusOrder(models.Model):
    # 1	Cancelado
    # 2	Pendiente
    # 3	Pago a Confirmar
    # 4	Pago Confirmado
    # 5	Enviado
    # 6	Completado
    # 7	Devolución
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=80, blank=True, null=True)  # Breve descripción


class PaymentMethod(models.Model):
    # 1 - Efectivo
    # 2 - Transferencia directa
    # 3 - Pagar en cuotas con tarjeta MERCADO PAGO API
    # 4 - Criptomoneda
    name = models.CharField(max_length=40)
    description = models.CharField(max_length=80, blank=True, null=True)
    time = models.IntegerField(default=2)
    is_active = models.BooleanField(default=True)
    
    
class ShipmentMethod(models.Model):
    # 1	Retiro en Local
    # 2	Dentro de Circunvalación
    # 3	Fuera de Circunvalación
    # 4	Puntos de Retiro Correo
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=80, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    

class ShipmentOrder(models.Model):
    method = models.ForeignKey('ShipmentMethod', on_delete=models.SET_NULL, null=True)
    
    # para en casos de envios completo
    address = models.CharField(max_length=120, blank=True, null=True)
    province = models.CharField(max_length=30, null=True, blank=True)
    city = models.CharField(max_length=30, null=True, blank=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    detail = models.CharField(max_length=150, blank=True, null=True)
    
    # para casos de retiro en local
    name_pickup = models.CharField(max_length=50, null=True, blank=True)
    dni_pickup = models.CharField(max_length=20, null=True, blank=True)
    
    def __str__(self):
        return self.method.name if self.method else "Sin método de envío"
    


class ItemOrder(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.IntegerField(default=0)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default='0.00')
    
    class Meta:
        verbose_name = "Ítem de orden"
        verbose_name_plural = "Ítems de orden"
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]
    
    @property
    def subtotal(self):
        """Subtotal calculado como propiedad (no se almacena en DB)"""
        subtotal = self.quantity * float(self.price)
        return float(subtotal)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class Order(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='orders')
    
    # Foreign Keys
    status = models.ForeignKey('StatusOrder', on_delete=models.SET_NULL, null=True, default=2)
    payment = models.ForeignKey('PaymentMethod', on_delete=models.SET_NULL, null=True)
    shipment = models.ForeignKey('ShipmentOrder', on_delete=models.SET_NULL, null=True)
    
    # Temporal fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expire_at = models.DateTimeField(null=True, blank=True)
    
    # Pricing fields moved from Invoice to Order
    shipment_cost = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    discount_coupon = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # total = float(
    #     sum(item.quantity * item.price) 
    #     + shipment..method.price 
    #     - discount (maybe coupon or from page product)
    #    )
    
    # Customer info
    name = models.CharField(max_length=100, blank=True, null=True)
    dni = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    cellphone = models.CharField(max_length=15, blank=True, null=True)
    detail_order = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']  # ordenar por fecha si agregas `de created`
    


class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name='invoice')
    user = models.ForeignKey('users.CustomUser', on_delete=models.PROTECT, related_name='invoices')
    
    # Datos administrativos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    invoice_number = models.CharField(max_length=30, unique=True, blank=True, null=True)
    
    # Campos calculados copiados de su orden.
    fiscal_total = models.DecimalField(max_digits=10, decimal_places=2)
    fiscal_type = models.CharField(
        max_length=1, 
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C')],
        default="B"
    )
    
    # Datos de procesamiento de pago (mercado pago, paypal, etc)
    payment_processor_data = models.JSONField(blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # maybe for analitycs
    total_mp = models.DecimalField(max_digits=10, decimal_places=2, default=0)

