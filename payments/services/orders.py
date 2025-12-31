from django.db.models import F
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from datetime import timedelta
from typing import Any
from decimal import Decimal

# orders app
from orders.models import (
    Order, OrderDraft, ShipmentMethod, 
    ShipmentOrder, PaymentMethod, ItemOrder
)
from orders.enums import StatusOrderEnum

# others apps
from cart.models import CartItem
from products.models.product import Product


class OrderService:
    """
    Service layer responsible for handling business logic related to orders.

    This service centralizes read-only operations for retrieving order data,
    keeping ORM queries out of views and improving reusability.
    """

    @staticmethod
    def get_user_orders(user) -> list[dict[str, Any]]:
        """
        Retrieve a list of orders belonging to a specific user.

        The query is optimized for list views (e.g. profile order history)
        by returning dictionaries instead of full model instances.

        Args:
            user (User): Authenticated Django user whose orders will be retrieved.

        Returns:
            list[dict]: A list of dictionaries with the following keys:
                - id (int): Order ID
                - created_at (datetime): Order creation timestamp
                - total (Decimal): Total amount of the order
                - status__name (str): Human-readable order status

        Notes:
            - Results are ordered by `updated_at` descending.
            - Authentication and authorization should be handled
              by the caller (view or API layer).
        """
        qs = (
            Order.objects
            .filter(user=user)
            .values('id', 'created_at', 'total', status_name=F('status__name'))
            .order_by('-updated_at')
        )

        return list(qs)
    
    
    @staticmethod
    def get_admin_orders(
        order_id: int | None = None, 
        status_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve orders for admin users with optional filters.

        Args:
            order_id (int | None): Filter by specific order ID.
            status_id (int | None): Filter by order status ID.

        Returns:
            list[dict[str, Any]]: List of order dictionaries.
        """
        qs = Order.objects.all()
            
        if order_id:
            qs = qs.filter(id=order_id)
            
        elif status_id:
            qs = qs.filter(status_id=status_id)

        return list(
            qs
            .values('id', 'created_at', 'total', status_name=F('status__name'))
            .order_by('-updated_at')
        )
    
    @staticmethod
    def create_order_pending(*, user, order_data: dict) -> Order:
        """
        Create a new pending order from the user's draft checkout.

        This method runs inside a single database transaction. If any step
        fails (for example, stock validation or order creation), the whole
        transaction is rolled back automatically.

        Steps:
        1. Lock the draft (prevent concurrent checkouts).
        2. Validate stock using the snapshot stored in the draft.
        3. Create the Order and its items.
        4. Mark the draft as USED so it can't be reused.

        Parameters
        ----------
        - user : User
            The user creating the order.
        - order_data : dict
            Data collected from the checkout form.

        Returns
        -------
        - Order:
            The created Order instance.
        """
        # todo se realiza en el mismo atomic, los distintos metodos lanzan raise que haran rollback
        # automatico en caso de error
        with transaction.atomic():

            # Lock the draft row so it cannot be modified concurrently
            # only() loads only the fields we really need
            draft = (
                OrderDraft.objects
                .select_for_update()
                .only("id", "cart", "status")
                .get(user=user, status="OPEN")
            )

            # Confirm stock and availability for each product in the draft snapshot
            dict_products_quantities = OrderService._confirm_stock_from_draft(draft.cart)

            # Create the order and its items
            order = OrderService._create_order_pending(
                user=user,
                order_data=order_data,
                products=dict_products_quantities["products"],
                products_ids_qty=dict_products_quantities["products_ids_qty"],
            )

            # último paso guardamos el draft a su nuevo estado
            # puede ser util para futuras analiticas, por ahora solo funciona de snapshot temporal
            draft.status = "USED"
            draft.save(update_fields=["status"])

            return order

    # -------------------- private methods
    @staticmethod
    def _create_order_pending(
        *,
        user,
        order_data: dict,
        products: dict,
        products_ids_qty: dict
    ) -> Order:
        """
        Create a new pending Order from the draft checkout data.

        This method assumes it is called inside a database transaction
        (managed by the caller). If anything fails, the caller’s transaction
        will roll back automatically.

        Responsibilities:
        -----------------
        1. Validate and fetch shipping & payment methods.
        2. Create a ShipmentOrder associated with the Order.
        3. Compute subtotal, discounts, and final total.
        4. Create the Order with status = PENDING.
        5. Create ItemOrder rows in bulk.
        6. Clear items from the user's cart.

        Parameters
        ----------
        user : User
            The owner of the order.
        order_data : dict
            Dictionary with customer, address and checkout data.
            (See view/service layer for full example structure)
        products : dict[int, Product]
            Products fetched and locked from database (from draft cart).
        products_ids_qty : dict[int, int]
            Quantities per product id.

        Returns
        -------
        Order
            The created order, already persisted in the database.

        Raises
        ------
        ValidationError
            If payment or shipping method is invalid.
            
        Example of order_data:
        ------
            order_data = {
                "first_name": "Lucas",
                "last_name": "Callamullo",
                "email": "lucas@hotmail.com",
                "cellphone": "3515437688",
                "dni": "41224335",
                "detail_order": "Por favor, entregar antes de las 18:00.",
                
                - NOTE if id_envio_method == '1': # this is only for retire local
                "name_retire": "Lucas",
                "dni_retire": "Callamullo",
                
                - NOTE if id_envio_method != '1': # Home delivery
                "province": "Córdoba",
                "city": "Córdoba Capital",
                "address": "Av. Colón 1234",
                "postal_code": "5000",
                "detail": "Departamento 2B",
                
                - NOTE this is for use to complete de order
                "shipping_method_id": "2", 
                "payment_method_id": "3"
            }
        """
        # .values() does not work with get(), so we simulate by using filter + first()
        shipping_method = (
            ShipmentMethod.objects
            .filter(id=order_data["shipping_method_id"])
            .values("id", "price")
            .first()
        )
        if not shipping_method:
            # propagar error 400 drf
            raise ValidationError("Método de envío no válido")

        payment_method = (
            PaymentMethod.objects
            .filter(id=order_data["payment_method_id"])
            .values("id", "time")
            .first()
        )
        if not payment_method:
            # propagar error 400 drf
            raise ValidationError("Método de pago no válido")

        # Create shipment entity linked to the order
        shipment = ShipmentOrder.objects.create(
            method_id=shipping_method["id"],
            name_pickup=order_data.get("name_retire", ""),
            dni_pickup=order_data.get("dni_retire", ""),
            address=order_data.get("address", ""),
            province=order_data.get("province", ""),
            city=order_data.get("city", ""),
            postal_code=order_data.get("postal_code", ""),
            detail=order_data.get("detail", ""),
        )

        # --- calcular subtotal primero ---
        subtotal = Decimal("0.00")

        for product_id, product in products.items():
            quantity = products_ids_qty.get(product_id)
            price_decimal = product.calc_discount_decimal()
            subtotal += price_decimal * quantity  # Decimal * int = Decimal

        # ---------------- Calcular total
        # maybe more logic like coupon model in the future
        discount_coupon = Decimal("0.00")
        total = subtotal + shipping_method["price"] - discount_coupon

        # Expiration window for order payment
        expire_at = timezone.now() + timedelta(hours=payment_method["time"])
        name = f'{order_data.get("first_name", "")} {order_data.get("last_name", "")}'

        # Create new Order
        new_order = Order.objects.create(
            user=user,
            status_id=StatusOrderEnum.PENDING,   # status por defecto pending
            payment_id=payment_method["id"],
            shipment=shipment,
            name=name,
            email=order_data.get("email", ""),
            cellphone=order_data.get("cellphone", ""),
            dni=order_data.get("dni", ""),
            detail_order=order_data.get("detail_order", ""),
            expire_at=expire_at,
            shipment_cost=shipping_method["price"],
            discount_coupon=discount_coupon,
            total=total,
        )

        # --------------- Crear order items asociados en bulk
        order_items = []

        for product_id, product in products.items():
            quantity = products_ids_qty.get(product_id)
            price_decimal = product.calc_discount_decimal()

            order_items.append(
                ItemOrder(
                    order=new_order,
                    product=product,
                    discount=product.discount,
                    original_price=product.price,
                    quantity=quantity,
                    final_price=price_decimal,
                )
            )

        ItemOrder.objects.bulk_create(order_items)

        # Remove items from cart only after successful order creation
        CartItem.objects.filter(
            product_id__in=products_ids_qty.keys(),
            cart__user=user
        ).delete()

        return new_order


    @staticmethod    
    def _confirm_stock_from_draft(cart_json: dict) -> dict:
        """
        Validate and reserve stock based on the items stored in the draft cart.

        This method works entirely inside the surrounding database transaction.
        If any validation fails, the raised exception rolls back all related
        operations automatically.

        Steps:
        1. Extract item list from the draft JSON snapshot.
        2. Build a `{product_id: quantity}` mapping.
        3. Fetch all products in bulk and lock them (SELECT ... FOR UPDATE)
        to prevent concurrent stock changes during checkout.
        4. Attempt to reserve stock for each product.
        5. Persist all stock changes in a single bulk update.

        Returns
        -------
        dict
            {
                "products": dict[int, Product],
                "products_ids_qty": dict[int, int]
            }

        Raises
        ------
        ValidationError
            If the cart is empty or there is insufficient stock.
        NotFound
            If a product referenced in the cart no longer exists.
        """

        items = cart_json.get("items")
        if not items:
            # propagar error con custom handler en core.exceptions 400 ->
            raise ValidationError("No hay productos agregados")

        # Map product_id -> quantity
        products_ids_qty = {
            item["id"]: item["quantity"]
            for item in items
        }

        # Fetch products in bulk and lock rows during the transaction
        products = (
            Product.objects
            .filter(id__in=products_ids_qty.keys())
            .select_for_update()
            .only("id", "name", "stock", "stock_reserved", "available", "price", "discount")
            .in_bulk()   # returns {id: Product}
        )

        modified = []

        for item in items:
            product_id = item["id"]

            # Defensive check — should not happen, but adds robustness
            if product_id not in products:
                # propagar error con custom handler en core.exceptions 404 ->
                raise NotFound(f"Product not found (id={product_id})")

            product = products[product_id]

            # Attempt to reserve stock
            if not product.make_stock_reserved(item["quantity"]):
                # propagar error con custom handler en core.exceptions 400 ->
                raise ValidationError(f"Stock insuficiente: {product.name}")

            modified.append(product)

        # Persist stock + reserved updates in one DB hit
        Product.objects.bulk_update(modified, ["stock", "stock_reserved"])

        return {
            "products": products,
            "products_ids_qty": products_ids_qty,
        }