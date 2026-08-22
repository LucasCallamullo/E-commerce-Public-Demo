from datetime import datetime
from django.db import transaction

from cart.models import Cart, CartItem


class CartService:

    @staticmethod
    def get_items_and_combine_carts(
        *,
        cart: Cart,
        shop_cart: dict | None = None
    ) -> dict:
        """
        Load all persisted items from the database and merge them with the
        in-session cart structure.

        Session cart structure (shop_cart):
            {
                "1": {
                    "id": 1,
                    "name": "Product 1",
                    "slug": "product-1",
                    "price": 20.99,
                    "image": "image_url_1.jpg",
                    "quantity": 2,
                    "stock": 3,
                    "discount": 10,   # always a percentage
                },
            }

        The resulting dictionary matches the session cart format. If there are
        no items, an empty dictionary is returned.

        Args:
            cart (Cart): Persistent cart stored in the database.
            shop_cart (dict | None): Cart currently stored in the user's session.

        Returns:
            dict: A normalized and synchronized cart structure ready for session use.
        """
        if shop_cart is None:
            shop_cart = {}

        # 1. Fetch all items related to this cart.
        #    Using the reverse relation improves performance and avoids extra queries.
        items = (
            cart.items
            .select_related("product")
            .only(
                "quantity",
                "product__id", "product__name", "product__slug", "product__price_ars",
                "product__main_image", "product__stock", "product__available", "product__discount_ars",
            )
            .filter(product__available=True)
        )

        # 2. Iterate once over the queryset and combine quantities safely.
        for item in items:
            product = item.product
            product_id = str(product.id)

            # Combined quantity between DB cart and session cart
            combined_qty = max(
                item.quantity,
                shop_cart.get(product_id, {}).get("quantity", 0),
            )

            # 3. Validate availability against stock
            is_available, stock = product.stock_or_available(combined_qty)

            # 4. Remove product from session if it is no longer available
            if not is_available:
                shop_cart.pop(product_id, None)
                continue

            # 5. Update with normalized, authoritative product data
            shop_cart[product_id] = {
                "id": product.id,
                "name": product.name,
                "slug": product.slug,
                "price": float(product.price_ars),
                "image": product.main_image,
                "quantity": min(combined_qty, stock),  # cap quantity to available stock
                "stock": stock,
                "discount": product.discount_ars,
            }

        # 6. Persist the synchronized items back to the DB
        CartService._save_items(cart=cart, shop_cart=shop_cart)

        # 7. Return the final session-ready cart
        return shop_cart
    
    
    @staticmethod
    def _save_items(*, cart: Cart, shop_cart: dict) -> None:
        """
        Persist cart items to the database based on the session cart.

        - Creates new items when they don't exist.
        - Updates quantities when they differ.
        - Removes items that were deleted from the session.

        The DB is considered the source of truth after synchronization.
        """

        # Ensure everything runs atomically for consistency
        with transaction.atomic():
            # 1. Prepare lookup dict of current DB items
            current_items = {
                str(item.product_id): item
                for item in cart.items.only("product_id", "quantity").all()
            }

            updates = []
            creates = []

            # 2. Compare DB items vs session cart
            for product_id, item_data in shop_cart.items():

                # Quantity should always exist, but we guard just in case
                quantity = item_data.get("quantity")
                if not quantity:
                    continue

                # Existing item → update quantity if needed
                if product_id in current_items:
                    item = current_items[product_id]
                    if item.quantity != quantity:
                        item.quantity = quantity
                        updates.append(item)

                # New item → stage for bulk creation
                else:
                    creates.append(
                        CartItem(
                            cart=cart,
                            product_id=product_id,
                            quantity=quantity,
                        )
                    )

            # 3. Remove items no longer present in the session cart
            to_delete = [
                item.pk
                for item in current_items.values()
                if str(item.product_id) not in shop_cart
            ]

            # 4. Execute bulk operations
            if updates:
                CartItem.objects.bulk_update(updates, ["quantity"])

            if creates:
                CartItem.objects.bulk_create(creates)

            if to_delete:
                CartItem.objects.filter(pk__in=to_delete).delete()

            # 5. Update cart timestamp
            # CartService.touch(cart=cart)


    @staticmethod
    def touch(*, cart: Cart) -> datetime:
        """
        Update only the `last_modified` timestamp of the cart.

        This is useful to mark the cart as changed without touching other fields.
        
        Returns:
            datetime: The updated `last_modified` timestamp.
        """
        cart.save(update_fields=["last_modified"])
        return cart.last_modified
