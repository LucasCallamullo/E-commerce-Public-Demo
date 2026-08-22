import logging
logger = logging.getLogger(__name__)

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import datetime

# services
from cart.services.cart_service import CartService
from cart.services.cart_item_service import CartItemService

# others apps
# from products.models.product import Product


class Carrito:
    def __init__(self, request):
        # Request-level shortcuts for easier access
        self.user = request.user
        self.session = request.session
        
        # Resolved by CartMiddleware.
        # - Authenticated user  -> Cart instance
        # - Anonymous user      -> None
        self.cart = request.cart
        
        # Cart ID stored in session (if any).
        # Used to correlate the session snapshot with the database cart.
        self.cart_id = self.session.get("cart_id", None)
        
        # Lightweight cart representation stored in session.
        # This acts as a snapshot/cache to avoid hitting the database
        # on every request or template render.
        self.carrito = self.session.get("carrito", {})
        
        # Timestamp of the last cart snapshot stored in session.
        # Used to detect whether the database cart has changed
        # since the last synchronization.
        self.last_modified = self.session.get("last_modified", None)
        
        # Initialize and synchronize cart state.
        # This method decides whether to:
        # - Use the session snapshot
        # - Rebuild from the database
        # - Migrate data between session and DB
        self._config_init()
        
        
    def _config_init(self):
        # ============================================================
        # Anonymous users: session-only cart (no database interaction)
        # ============================================================
        if not self.user.is_authenticated:
            # If the user logged out, the previously associated DB cart
            # is no longer accessible, but we keep the session cart
            # so the user can continue browsing or shopping.
            if self.cart_id is not None:
                self._save_session()
                return
            
        # =====================================================================
        # Cart synchronization logic (multiple tabs, sessions, or stale data)
        # =====================================================================
        
        # If there is no cart_id or no timestamp snapshot,
        # we cannot trust the session state.
        # This usually happens:
        # - On first login
        # - On first cart access after authentication
        # In this case, rebuild the session cart from the database.
        if not self.cart_id or not self.last_modified:
            logger.debug(
                "[ANONYMUS USER] estamos en first login CART: %s", self.cart
            )
            self.migrate_carrito_to_cart_db()
            return
        
        # At this point:
        # - The user is authenticated
        # - A cart exists in the database (resolved by the middleware)
        # - A session snapshot exists
        #
        # Compare timestamps to detect external changes
        # (e.g. another tab or concurrent session).
        if not self.cart:
            return
        
        if self.cart.last_modified > parse_datetime(self.last_modified):
            logger.debug(
                "[CART SYNC] SE HIZO SYNCRHO CON DB ENTRE TABS -> db=%s session=%s",
                self.cart.last_modified,
                self.last_modified,
            )
            # The database cart is newer than the session snapshot.
            # Rebuild the session cart to stay consistent.
            self.migrate_carrito_to_cart_db(first_login=False)
            
        elif self.cart.last_modified < parse_datetime(self.last_modified):
            logger.debug(
                "[CART SYNC] FIRST LOG IN, AFTER OBJECTS ON CART SO WE HAVE LAST_MODIFIED -> db=%s session=%s",
                self.cart.last_modified,
                self.last_modified,
            )
            # The database cart is newer than the session snapshot.
            # Rebuild the session cart to stay consistent.
            self.migrate_carrito_to_cart_db(first_login=True)
            
        else:
            logger.debug(
                "[CART SYNC] SON IGUALES NO TOCA DB -> db=%s session=%s",
                self.cart.last_modified,
                self.last_modified,
            )

    # ------------------ Methods n properties ---------------------------

    def migrate_carrito_to_cart_db(self, first_login: bool = False):
        """
        Synchronizes the session cart snapshot with the database cart.

        This method assumes:
        - The user is authenticated
        - `self.cart` has been resolved by CartMiddleware
        """
        if not self.cart:
            # Defensive guard (should not normally happen)
            return
        
        # Merge session snapshot with database cart
        self.carrito = CartService.get_items_and_combine_carts(
            cart=self.cart, 
            shop_cart=self.carrito if first_login else None
        )
        
        last_modified_at = CartService.touch(cart=self.cart)

        # Persist updated snapshot back into session
        self._save_session(last_modified=last_modified_at)
        
    # -----------------------       private methods      --------------
        
    def _save_session(self, last_modified: datetime = None):
        """
        Saves the cart snapshot to the session.

        The session timestamp is aligned with the database cart timestamp
        when available, ensuring reliable multi-tab synchronization.
        
        Args:
            last_modified (optional): An optional timestap type datetime
            to set from db like source of truth.
        """
        # save the updated cart on the session
        self.session["carrito"] = self.carrito

        # Store the last modification time for cross-tab synchronization
        if last_modified:
            # DB is source of truth
            self.session["last_modified"] = last_modified.isoformat()
        else:
            # Anonymous user or no DB change
            self.session["last_modified"] = timezone.now().isoformat()

        # Store the updated cart ID in the session
        self.session["cart_id"] = self.cart_id
        
        # save changes on session
        self.session.modified = True
        
        
    def _save_item(self, item_data: dict, action: str) -> None | datetime:
        """ sincroniza con la base de datos si es necesario. """
        
        # Update the cart in the database if the user is authenticated, has cart by the
        # middleware and previouis cart_id, in general he has all() if is authenticated
        if not self.user.is_authenticated or not self.cart_id or not self.cart:
            return None
        
        # Delegamos toda la lógica al modelo CartItemService y el mismo nos devuelve un timestap
        # utilizar en _save_session()
        if action == 'create':
            return CartItemService.add_item_cart(
                cart = self.cart,
                item_data = item_data
            )
            
        elif action == 'patch':
            return CartItemService.update_item_cart(
                cart = self.cart,
                item_data = item_data
            )
            
        elif action == 'delete':
            return CartItemService.delete_item_cart(
                cart = self.cart,
                item_data = item_data
            )
            
        # no debería pasar pero bueno hacemos explicito el return
        return None
        
    # -----------------------   crud session      --------------    
        
    def add_product(self, product, quantity: int = 1) -> str:
        """
        Add a product to the cart, updating both the session and database.

        If the product is already in the cart, its quantity is incremented.
        Otherwise, a new entry is created.

        Args:
            product (Product): The product instance to add.
            quantity (int, optional): Number of units to add. Defaults to 1.

        Returns:
            str: Action performed, either 'create' (new item) or 'patch' (quantity updated).
        """
        product_id = str(product.id)
        
        # 1. Update the cart snapshot in the session
        if product_id not in self.carrito:
            self.carrito[product_id] = {
                "id": product.id,
                "name": product.name,
                "slug": product.slug,
                "price": float(product.price_ars),
                "image": product.main_image,
                "quantity": quantity,
                "stock": product.stock,
                "discount": product.discount_ars,
            }
            action = 'create'
        else:
            self.carrito[product_id]["quantity"] += quantity
            action = 'patch'
        
        # 2. Persist changes to the database and get the real last_modified timestamp
        last_modified = self._save_item(
            item_data=self.carrito.get(product_id),
            action=action
        )

        # 3. Save updated cart snapshot in the session using DB timestamp
        self._save_session(last_modified)
        
        return action

    def subtract_product(self, product, quantity: int = 1) -> str:
        """
        Reduce the quantity of a product in the cart. 

        If the resulting quantity is greater than zero, the cart item is updated.
        If the quantity drops to zero or below, the item is removed from the cart.

        Args:
            product (Product): The product instance to subtract.
            quantity (int, optional): Number of units to subtract. Defaults to 1.

        Returns:
            str: Action performed:
                - 'patch': quantity updated
                - 'delete': item removed
                - 'not_found': product not present in the cart
        """
        product_id = str(product.id)
        
        # Product not in cart (edge case handling)
        if product_id not in self.carrito:
            return 'not_found'
        
        # 1. Calculate new quantity for robustness
        new_quantity = self.carrito[product_id]["quantity"] - quantity
        if new_quantity > 0:
            self.carrito[product_id]["quantity"] = new_quantity
            snapshot = self.carrito[product_id]
            action = 'patch'
        else:
            # 1.a Remove the product if quantity reaches 0
            snapshot = self.carrito.pop(product_id)
            action = 'delete'
        
        # 2. Persist changes to the database and get actual timestamp
        last_modified = self._save_item(
            item_data=snapshot, 
            action=action
        )

        # 3. Update session snapshot using DB timestamp
        self._save_session(last_modified)
        
        return action

    def delete_product(self, product_id: int) -> str:
        """
        Remove a product from the cart.

        This method will remove the product entirely from the session cart
        and the database.

        Args:
            product (Product): The product instance to remove.

        Returns:
            str: Action performed:
                - 'delete': product successfully removed
                - 'not_found': product was not present in the cart (should never happen)
        """
        product_id = str(product_id)
        
        # Edge case: product not found in cart (should not occur)
        if product_id not in self.carrito:
            return 'not_found'
        
        snapshot = self.carrito.pop(product_id)

        # 1. Persist changes to DB and get the actual timestamp
        last_modified = self._save_item(
            item_data=snapshot, 
            action='delete'
        )
        
        # 2. Update session snapshot using DB timestamp
        self._save_session(last_modified)
        
        return 'delete'

    def clear(self):
        """
            Limpia el carrito.
        """
        # save the updated cart on the session
        self.session["carrito"] = {}

        # Store the last modification time for cross-tab synchronization
        if self.cart:
            last_modified_at = CartService.touch(cart=self.cart)
            self.session['last_modified'] = last_modified_at.isoformat()
        else:
            self.session['last_modified'] = timezone.now().isoformat()

        # Store the updated cart ID in the session
        self.session["cart_id"] = self.cart_id
        
        # save changes on session
        self.session.modified = True
        
    # ------------------------- helpers carrito -------------------------

    def get_cart_serializer(self) -> dict:
        """
        Return a dict with:
            - 'items': list of cart items
            - 'total_price': total price without discounts
            - 'total_price_discount': total price with discounts applied
            - 'total_quantity': total items
        """
        cart_items = []
        total_price = 0
        total_price_discount = 0
        total_items = 0

        for values in self.carrito.values():
            # necesario parsea Decimal a Float porque sino no lo acepta Json
            price = float(values['price'])
            quantity = int(values['quantity'])
            discount = int(values.get('discount', 0))

            item_total = price * quantity
            item_total_discount = item_total * (1 - discount / 100)

            cart_items.append({
                'id': values['id'],
                'name': values['name'],
                'slug': values['slug'],
                'price': price,
                'image': values['image'],
                'quantity': quantity,
                'stock': values['stock'],
                'discount': discount,  # porcentual
            })

            total_price += item_total
            total_price_discount += item_total_discount
            total_items += quantity

        return {
            'items': cart_items,
            'total_price': round(total_price, 2),
            'total_price_discount': round(total_price_discount, 2),
            'total_quantity': total_items,
        }
        
        
    def sync_cart_on_logout(self, cart: dict):
        """
        Handles synchronization when a user logs out, transferring the
        cart items from the previous (authenticated) session to the new
        anonymous session.

        Notes:
            - This function is directly coupled to the API View located at
            users/views/api/session.py
        """
        # Restore cart into the new anonymous session
        self.session["carrito"] = cart

        # Anonymous user — update last modification timestamp
        self.session["last_modified"] = None

        # No DB cart associated anymore
        self.session["cart_id"] = None

        # Persist session changes
        self.session.modified = True