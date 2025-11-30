

from cart.models import Cart
from django.utils import timezone
from django.utils.dateparse import parse_datetime


class Carrito:
    def __init__(self, request):
        self.user = request.user
        self.session = request.session
        
        # Esto viene del middleware, puede ser None si no está autenticado
        self.cart = request.cart
        
        self.carrito = self.session.get("carrito", {})
        
        self.cart_id = self.session.get("cart_id", None)
        self.last_modified = self.session.get('last_modified', None)
        
        # Logica para manejar sincronizacion entre carritos de disintas pestañas, sesiones
        if self.user.is_authenticated:
            
            # Esto se dara post logeo realmente, porque recien ahi tendra un cart_id
            if self.cart_id and self.last_modified:
                
                # recuperramos Cart con el realted_name
                # cart = self.user.carrito
                cart = request.cart  
                
                # Compara la fecha de la última modificación
                last_modified = parse_datetime(self.last_modified)
                if cart.last_modified > last_modified:
                    self.migrate_carrito_to_cart_db(cart=cart)

            # Cuando el cart_id is None, solo ocurre una vez antes de logearse
            else: 
                # recupera los datos desde la base de datos
                self.migrate_carrito_to_cart_db()

        # Si no esta autenticado el usuario no manejamos la base de datos
        else:
            # Si se deslogea no accede al Cart que estaba asociado antes
            # pero se queda con el carrito con los items en la session por si quisiera seguir comprando o algo 
            if self.cart_id is not None:
                self.save_session()
                
                
    # ======================================================================
    #                   Methods n properties
    # ======================================================================
    def migrate_carrito_to_cart_db(self, cart=None):
        """ Migra el carrito de la sesión al carrito de base de datos cuando el usuario se registra. """
        if cart is None:
            cart, _ = Cart.objects.get_or_create(user=self.user)
            
        # obtenemos un diccionario para combinar con el self.carrito de la sesion si existiera
        self.carrito = cart.get_items_and_combine_carts(self.carrito)
        self.save_session(cart_id=cart.id)
        
        
    def get_cart_serializer(self) -> dict:
        """
        Return a dict with:
            - 'cart': list of cart items (each is a dict)
            - 'cart_price': total price (float)
            - 'cart_quantity': total items (int)
        """
        cart_items = []
        total_price = 0
        total_items = 0

        if self.carrito:
            for values in self.carrito.values():
                item = {
                    'id': int(values['id']),
                    'name': values['name'],
                    'slug': values['slug'],
                    'price': float(values['price']),
                    'image': values['image'],
                    'quantity': int(values['quantity']),
                    'stock': int(values['stock']),
                }
                cart_items.append(item)
                total_price += item['price'] * item['quantity']
                total_items += item['quantity']

        dict_context = {
            'cart': cart_items,
            'cart_price': float(total_price),
            'cart_quantity': int(total_items),
        }
        return dict_context

    @property
    def total_price(self) -> float:
        """
        Returns the total sum of all item prices in the cart.

        Notes:
            - The 'self.total' attribute is used to calculate this value only once 
            via the context processor, and then it is passed to templates as context.
        """
        t = sum(item['price'] * item['quantity'] for item in self.carrito.values()) if self.carrito else 0
        return float(t)


    @property
    def total_items(self) -> int:
        """
        Returns the total quantity of all products in the cart.
        """
        t = sum(item['quantity'] for item in self.carrito.values()) if self.carrito else 0
        return t


    @property
    def items(self):
        """
        Returns the cart items as a (key, value) dictionary pair 
        so it can be easily used in Django views and templates.
        """
        return self.carrito.items()


    # ======================================================================
    #                   CRUD ACTIONS Cart
    # ======================================================================
    def save_session(self, cart_id=None):
        """
        Saves the cart to the session and stores additional data 
        to support synchronization across multiple browser tabs.

        Args:
            cart_id (optional): An optional cart ID to store in the session.
        """
        # save the updated cart on the session
        self.session["carrito"] = self.carrito

        # Store the last modification time for cross-tab synchronization
        self.session['last_modified'] = timezone.now().isoformat()

        # Store the updated cart ID in the session
        self.cart_id = cart_id
        self.session["cart_id"] = self.cart_id
        
        # save changes on session
        self.session.modified = True
        
        
    def save_item(self, product=None):
        """ sincroniza con la base de datos si es necesario. """
        
        # Update the cart in the database if the user is authenticated
        if not self.user.is_authenticated and not self.cart_id and not self.cart:
            return
        
        cart = self.cart
        
        # cart = Cart.objects.get(id=self.cart_id)
        product_id = str(product.id)
        item_data = self.carrito.get(product_id)    # product_data or None
        
        # Delegamos toda la lógica al modelo Cart
        cart.sync_item_from_session(
            product=product,
            item_data=item_data
        )
        
    def add_product(self, product, quantity=1) -> bool:
        """
        Adds a product to the cart (both session and database).

        Args:
            product: The product instance to add.
            quantity (int, optional): Number of units to add. Defaults to 1.

        Returns:
            bool: Returns True if the product was successfully added.
        """
        product_id = str(product.id)
        
        # Update the cart in the session
        if product_id not in self.carrito:
            self.carrito[product_id] = {
                "id": product.id,
                "name": product.name,
                "slug": product.slug,
                "price": float(product.price),
                "image": product.main_image,
                "quantity": quantity,
                "stock": product.stock,
            }
        else:
            self.carrito[product_id]["quantity"] += quantity
        
        # save data in session
        self.save_session(cart_id=self.cart_id)
        
        # save item in CartItem db
        self.save_item(product=product)


    def subtract_product(self, product, quantity=1) -> bool:
        """
        Reduce la cantidad de un producto del carrito.
        Al final retornara un bool que nos servira para indicar distintos tipo de mensajes
        segun la peticion ajax realizadas en views.py
        """
        product_id = str(product.id)
        
        if self.carrito[product_id]["quantity"] > 1:
            self.carrito[product_id]["quantity"] -= quantity
            delete_item = False
        else:
            # eliminar el producto si la cantidad llega a 0
            del self.carrito[product_id]
            delete_item = True
            
        # guardamos los cambios en el carrito de la session
        self.save_session(cart_id=self.cart_id)
        
        # save item in CartItem db
        self.save_item(product=product)
        
        # este retorno nos sirve para los mensajes de las alertas
        return delete_item


    def delete_product(self, product) -> bool:
        """
            Elimina un producto del carrito.
            No se realizan verificaciones de las key debido a que la logica no permitiría 
            que sucedieran
        """
        product_id = str(product.id)
        
        # Consultamos si por algun motivo no existiera el product-id en el carrito
        if product_id not in self.carrito:
            return False
        
        del self.carrito[product_id]
        
        # guardamos los cambios en el carrito de la session
        self.save_session(cart_id=self.cart_id)
        
        # save item in CartItem db
        self.save_item(product=product)

        return True

    
    def clear(self):
        """
            Limpia el carrito.
        """
        # save the updated cart on the session
        self.session["carrito"] = {}

        # Store the last modification time for cross-tab synchronization
        self.session['last_modified'] = timezone.now().isoformat()

        # Store the updated cart ID in the session
        self.session["cart_id"] = None
        
        # save changes on session
        self.session.modified = True
        # self.carrito = {}
        # self.save(action='clear')
        

