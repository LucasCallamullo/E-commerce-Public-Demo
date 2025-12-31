import pytest
from decimal import Decimal
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from orders.services.orders import OrderService
from orders.models import OrderDraft, Order, ItemOrder

# others apps
from products.models.product import Product
from cart.models import Cart, CartItem


@pytest.mark.django_db
def test_create_order_pending_success(user, cart):

    # --- producto
    product = Product.objects.create(
        name="Peluche Espeon",
        price=Decimal("5000"),
        discount=10,
        stock=10,
        stock_reserved=0,
        available=True,
    )

    # --- carrito (draft snapshot)
    draft = OrderDraft.objects.create(
        user=user,
        # status="OPEN", default open
        cart={
            "items": [
                {
                    "id": product.id,
                    "name": product.name,
                    "quantity": 2,
                    "price": 5000,
                    "discount": 10,
                }
            ],
            "total_price": 10000,
            "total_price_discount": 9000,
            "total_quantity": 2,
        }
    )

    # --- order_data simulando request
    order_data = {
        "first_name": "Lucas",
        "last_name": "Callamullo",
        "email": "lucas@test.com",
        "cellphone": "123456",
        "dni": "41224335",
        "detail_order": "probando",

        "province": "Cordoba",
        "city": "Cordoba",
        "address": "Colon 123",
        "postal_code": "5000",

        "shipping_method_id": "1",
        "payment_method_id": "1",
    }

    # --- ejecutar servicio
    order = OrderService.create_order_pending(
        user=user,
        order_data=order_data,
    )

    # ---------------- ASSERTS ----------------
    assert Order.objects.count() == 1
    assert ItemOrder.objects.count() == 1

    item = ItemOrder.objects.first()
    assert item.quantity == 2
    assert item.product == product

    # hace otra consulta a la base y vuelve a cargar el objeto desde la DB, 
    # sobrescribiendo los valores que tiene en memoria.
    product.refresh_from_db()
    assert product.stock_reserved == 2
    assert product.stock == 8

    # carrito borrado
    assert CartItem.objects.filter(product=product).count() == 0
    

@pytest.mark.django_db
def test_create_order_fails_if_no_stock(user, cart):

    product = Product.objects.create(
        name="Peluche",
        price=1000,
        discount=0,
        stock=1,
        stock_reserved=0,
        available=True,
    )

    OrderDraft.objects.create(
        user=user,
        status="OPEN",
        cart={
            "items": [
                {"id": product.id, "quantity": 5}
            ]
        }
    )

    order_data = {
        "shipping_method_id": "1",
        "payment_method_id": "1",
    }

    with pytest.raises(ValidationError):
        OrderService.create_order_pending(user=user, order_data=order_data)

    # nada se creó
    assert Order.objects.count() == 0

    product.refresh_from_db()
    assert product.stock_reserved == 0
