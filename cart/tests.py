from django.test import TestCase

# Create your tests here.
from cart.carrito import Carrito
from cart.models import Cart, CartItem
from products.models import Product
from django.contrib.auth import get_user_model


class CartModelTest(TestCase):
    def setUp(self):
        # Crea un usuario de prueba
        self.user = get_user_model().objects.create_user(email="testuser@gmail.com", password="password123")
        
        # Crea productos de prueba
        self.producto1 = Product.objects.create(name="Product 1", stock=10, price=100)
        self.producto2 = Product.objects.create(name="Product 2", stock=5, price=200)
        
        # Crea un carrito asociado al usuario
        self.carrito = Cart.objects.create(user=self.user)

    def test_agregar_item_al_carrito(self):
        # Agregar un producto al carrito
        item = CartItem.objects.create(cart=self.carrito, product=self.producto1, quantity=2)

        # Verificar que el ítem se haya añadido correctamente
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.product, self.producto1)

    def test_eliminar_item_del_carrito(self):
        # Agregar y eliminar un producto
        item = CartItem.objects.create(cart=self.carrito, product=self.producto1, quantity=2)
        item.delete()

        # Verificar que el carrito esté vacío
        self.assertEqual(self.carrito.items.count(), 0)

    def test_carrito_asociado_a_usuario(self):
        # Verificar que el carrito está correctamente asociado al usuario
        self.assertEqual(self.carrito.user, self.user)
