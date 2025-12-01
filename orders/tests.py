from django.test import TestCase

# Create your tests here.
from orders.models import (
    OrderStatus, PaymentMethod, OrderItem, Order, Envio, Factura, TipoFactura
)
from products.models import Product
from users.models import CustomUser


class OrderModelsTest(TestCase):

    def setUp(self):
        # Configuración inicial que se ejecuta antes de cada prueba
        self.user = CustomUser.objects.create_user(email="test@example.com", password="password")
        self.product = Product.objects.create(name="Producto de prueba", price=100.0)
        self.status = OrderStatus.objects.create(name="Pendiente", description="Pedido pendiente")
        self.payment = PaymentMethod.objects.create(name="Tarjeta", description="Pago con tarjeta")
        self.envio = Envio.objects.create(
            name="Envío a domicilio",
            description="Entrega en la dirección del cliente.",
            adress="Calle Falsa 123",
            province="Buenos Aires",
            city="La Plata",
            postal_code=1900,
        )
        self.factura = Factura.objects.create(
            tipo="A",
            buyer_name="Juan Pérez",
            buyer_dni=12345678,
            description="Factura por compra online."
        )
        self.order = Order.objects.create(
            user=self.user,
            status=self.status,
            payment=self.payment,
            envio=self.envio,
            factura=self.factura,
            total=200.0
        )

    def test_order_status_creation(self):
        """Testea la creación de un estado de pedido."""
        self.assertEqual(self.status.name, "Pendiente")
        self.assertEqual(self.status.description, "Pedido pendiente")
        self.assertEqual(str(self.status), "Pendiente")

    def test_payment_method_creation(self):
        """Testea la creación de un método de pago."""
        self.assertEqual(self.payment.name, "Tarjeta")
        self.assertEqual(self.payment.description, "Pago con tarjeta")
        self.assertTrue(self.payment.is_active)
        self.assertEqual(str(self.payment), "Tarjeta")

    def test_envio_creation(self):
        """Testea la creación de un envío."""
        self.assertEqual(self.envio.name, "Envío a domicilio")
        self.assertEqual(self.envio.adress, "Calle Falsa 123")
        self.assertEqual(self.envio.city, "La Plata")
        self.assertEqual(self.envio.postal_code, 1900)
        self.assertEqual(str(self.envio), "Envío a domicilio")

    def test_factura_creation(self):
        """Testea la creación de una factura."""
        self.assertEqual(self.factura.tipo, TipoFactura.A)
        self.assertEqual(self.factura.buyer_name, "Juan Pérez")
        self.assertEqual(self.factura.buyer_dni, 12345678)

    def test_order_item_creation(self):
        """Testea la creación de un ítem de pedido y calcula el subtotal."""
        order_item = OrderItem.objects.create(order=self.order, product=self.product, quantity=2, price=50.0)
        self.assertEqual(order_item.subtotal, 100.0)
        self.assertEqual(str(order_item), "2 x Producto de prueba")

    def test_order_creation(self):
        """Testea la creación de un pedido con datos relacionados."""
        self.assertEqual(self.order.total, 200.0)
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.status, self.status)
        self.assertEqual(self.order.payment, self.payment)
        self.assertEqual(str(self.order), f"Pedido #{self.order.id} - {self.user.email}")
