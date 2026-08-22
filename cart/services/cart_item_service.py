import logging
logger = logging.getLogger(__name__)

from datetime import datetime
from cart.services.cart_service import CartService
from cart.models import Cart, CartItem


class CartItemService:
    """
    Service layer for operations related to CartItem.

    Centralizes all persistence logic so views/serializers/controllers
    stay focused on orchestration and validation instead of database details.
    """

    @staticmethod
    def update_item_cart(*, cart: Cart, item_data: dict) -> None | datetime:
        """
        Update the item quantity in the cart — only if it actually changed.

        Returns:
            datetime | None:
                - The updated `last_modified` timestamp when the cart changes.
                - None when nothing was modified.

        Notes:
            This path assumes the CartItem already exists (normal flow).
            If it does not exist, we log a warning because it indicates a
            potential synchronization issue between session and database.
        """
        try:
            cart_item = CartItem.objects.get(
                cart=cart,
                product_id=item_data["id"],
            )

            # Only hit the database when the value actually changes.
            if cart_item.quantity != item_data["quantity"]:
                cart_item.quantity = item_data["quantity"]
                cart_item.save(update_fields=["quantity"])

                # Touch the cart so consumers know something changed.
                return CartService.touch(cart=cart)

        except CartItem.DoesNotExist:
            # This should never happen under normal flow.
            # If it happens, it usually means stale state / desynchronization.
            logger.warning(
                "CartItem out of sync (cart_id=%s, product_id=%s)",
                cart.id,
                item_data.get("id"),
            )

        return None
    
    @staticmethod
    def add_item_cart(*, cart: Cart, item_data: dict) -> datetime:
        """
        Create a new CartItem in the database for this cart.

        This method assumes validation has already been done at a higher level
        (e.g., stock checks, product existence, duplicated items, etc.).

        Returns:
            datetime:
                The updated `last_modified` timestamp of the cart.
        """
        CartItem.objects.create(
            cart=cart,
            product_id=item_data["id"],
            quantity=item_data["quantity"]
        )

        # Touch the cart so consumers know something changed.
        return CartService.touch(cart=cart)

    @staticmethod
    def delete_item_cart(*, cart: Cart, item_data: dict) -> datetime:
        """
        Remove a product from the cart.

        Deletes the matching CartItem (if any) and updates the cart timestamp
        to signal that its state has changed.

        Returns:
            datetime: Updated `last_modified` timestamp from the cart.
        """
        # Delete only the item matching this cart + product
        CartItem.objects.filter(
            cart=cart,
            product_id=item_data["id"],
        ).delete()

        # Persist cart state change
        return CartService.touch(cart=cart)