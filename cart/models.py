from django.db import models

# Create your models here.
from users.models import CustomUser
from products.models import Product

from django.db import transaction
from django.utils import timezone


class Cart(models.Model):
    user = models.OneToOneField('users.CustomUser', on_delete=models.CASCADE, related_name="carrito")
    # auto_now = django lo actualiza en cada etapa que se guarda
    last_modified = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['last_modified']),  # Opcional, redundante con db_index=True
        ]
        
    def get_items_and_combine_carts(self, shop_cart: dict = {}) -> dict:
        """
        Recupera todos los items guardados en la db, y los transforma al diccionario que utiliza carrito de la session
        
        Estructura del carrito de la session (shop_cart):
            self.carrito = {
                "1": {
                    "id": 1,
                    "name": "Product 1",
                    "price": 20.99,
                    "image": "image_url_1.jpg",
                    "quantity": 2,
                },
            }
        
        Returns:
            un diccionario adaptado al formato del self.carrito de la session que utiizamos,
            lo devolverá vacío o cargado segun contenga o no items
        """
        
        # 1. recuperamos el objeto producto con todos sus atributos
        items = (
            self.items
            .select_related('product')
            .only(
                'quantity',
                'product__id', 'product__name', 'product__slug', 'product__price',
                'product__main_image', 'product__stock', 'product__available'
            )
            .filter(product__available=True)
        )
        
        for item in items:
            product = item.product
            product_id = str(product.id)
            
            # 2. sería la cantidad combinada de ambos carritos
            combined_qty = max(item.quantity, shop_cart.get(product_id, {}).get('quantity', 0))
            
            # 3. consultamos disponibilidad de la cantidad combinada
            is_available, stock = product.stock_or_available(combined_qty)
            
            # 4. quito el producto del nuevo carrito directamente si no estuviese ya disponible
            if not is_available:
                shop_cart.pop(product_id, None)
                continue
            
            # 5. si llegamos hasta aca actualizamos con los datos del producto
            shop_cart[str(product.id)] = {
                "id": product.id,
                "name": product.name,
                "slug": product.slug,
                "price": float(product.price),
                "image": product.main_image,
                'quantity': min(combined_qty, stock),    # colocamos la cantidad maxima disponible en esta instancia
                'stock': stock,
            }
            
        # 6. Actualizamos los items en el Cart de la db basado en los id obtenidos
        self.save_items(shop_cart)
           
        # 7. retornamos el dict para ser utilizado como cart de la session
        return shop_cart
    
    def save_items(self, shop_cart: dict) -> None:
        """
        Actualiza los items del carrito en la base de datos según el diccionario de la sesión.
        - Crea nuevos items si no existen.
        - Actualiza cantidades si cambian.
        - Elimina items removidos de la sesión.
        """
        with transaction.atomic():  # Asegura consistencia
            # 1. Preparar datos para bulk_update/create
            current_items = {
                str(item.product_id): item 
                for item in self.items.only('product_id', 'quantity').all()
            }
            updates = []
            creates = []
            
            # 2. Comparar con shop_cart
            for product_id, item_data in shop_cart.items():
                print(f'producto id: {product_id}, y cantidad: {item_data['quantity']}')
                quantity = item_data['quantity']
                
                if product_id in current_items:  # Item existente
                    item = current_items[product_id]
                    if item.quantity != quantity:
                        item.quantity = quantity
                        updates.append(item)
                else:  # Nuevo item
                    creates.append(
                        CartItem(
                            cart=self,
                            product_id=product_id,
                            quantity=quantity
                        )
                    )
            
            # 3. Eliminar items no presentes en shop_cart (opcional)
            to_delete = [
                item.pk for item in current_items.values() 
                if str(item.product_id) not in shop_cart
            ]
            
            # 4. Ejecutar operaciones masivas
            if updates:
                CartItem.objects.bulk_update(updates, ['quantity'])
            if creates:
                CartItem.objects.bulk_create(creates)
            if to_delete:
                CartItem.objects.filter(pk__in=to_delete).delete()
            
            # 5. Actualizar last_modified
            self.touch()
            
    def sync_item_from_session(self, product: Product, item_data: dict = None):
        """
        Sincroniza un producto del carrito de sesión con la base de datos.
        - Si item_data es None, elimina el producto.
        - Si existe, actualiza o crea el CartItem.
        """
        if item_data is None:
            self.remove_product(product)
        else:
            self.add_or_update_product(product, item_data['quantity'])
        
        self.touch()  # Actualiza last_modified

    def add_or_update_product(self, product: Product, quantity: int):
        """Añade o actualiza un producto en el carrito."""
        cart_item, _ = CartItem.objects.get_or_create(
            cart=self,
            product=product
        )
   
        cart_item.update_quantity(quantity)

    def remove_product(self, product: Product):
        """Elimina un producto del carrito."""
        CartItem.objects.filter(cart=self, product=product).delete()

    def touch(self) -> None:
        """Actualiza solo el campo last_modified."""
        self.save(update_fields=['last_modified'])
    
        
class CartItem(models.Model):
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE)
    quantity  = models.PositiveIntegerField(default=1)
    
    class Meta:
        indexes = [ models.Index(fields=['cart', 'product']), ]
        
    def update_quantity(self, new_quantity: int) -> None:
        """Actualiza la cantidad solo si es diferente."""
        if self.quantity != new_quantity:
            self.quantity = new_quantity
            self.save(update_fields=['quantity'])

    def remove(self) -> None:
        """Elimina el ítem del carrito."""
        self.delete()
        
        
        
        
    def update_item_from_cart(self, action='remove', quantity=0):
        # este mnetodo capaz ya no se utiliza revisar
        if action == 'update':
            self.quantity = quantity
            self.save()
            
        elif action == 'delete':
            self.delete()
        



""" 

def update_cart_db(self, product=None, action='nada', quantity=0):
        ""
        Centraliza todas las actualizaciones del carrito con un método en el mismo modelo.
        Para asegurar la consistencia de la base de datos, se utiliza el método atomic().

        Args:
            product (Product): El producto que se está agregando, eliminando o modificando en el carrito.
            action (str, optional): La acción a realizar. Los valores posibles son:
                - 'add': Agregar el producto al carrito.
                - 'remove': Eliminar el producto del carrito.
                - 'substract': Restar la cantidad del producto en el carrito.
                - 'clear': Limpiar el carrito despues de procesar el pago
                Por defecto es 'nada', lo que no realiza ninguna acción.
            qty (int, optional): La cantidad a agregar o restar. El valor predeterminado es 0.

        Returns:
            None
        ""
        with transaction.atomic():
            if action == 'add':
                cart_item, _ = self.items.get_or_create(product=product)
                cart_item.quantity = quantity
                cart_item.save()
            
            elif action == 'remove':
                self.items.filter(product=product).delete()
            
            elif action == 'substract':
                cart_item = self.items.filter(product=product).first()
                
                if cart_item.quantity > 1:
                    cart_item.quantity -= quantity
                    cart_item.save()
                else:
                    cart_item.delete()
            
            elif action == 'clear':
                self.items.all().delete()
                
            # actualizamos para la sincronizacion entre pestañas    
            self.last_modified = timezone.now()
            self.save()

"""