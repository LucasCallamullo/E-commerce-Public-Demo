

import pytest
from cart.models import CartItem
from cart.services.cart_item_service import CartItemService


@pytest.mark.django_db
def test_update_item_cart_updates_quantity(cart, product):
    # arrange
    cart_item = CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=1
    )

    item_data = {
        'id': product.id,
        'quantity': 3
    }

    # act
    touched_at = CartItemService.update_item_cart(
        cart=cart,
        item_data=item_data
    )

    # assert
    cart_item.refresh_from_db()
    assert cart_item.quantity == 3
    assert touched_at is not None


@pytest.mark.django_db
def test_update_item_cart_does_nothing_if_quantity_same(cart, product):
    CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=2
    )

    item_data = {
        'id': product.id,
        'quantity': 2
    }

    touched_at = CartItemService.update_item_cart(
        cart=cart,
        item_data=item_data
    )

    assert touched_at is None


@pytest.mark.django_db
def test_add_item_cart_creates_cart_item(cart, product):
    item_data = {
        'id': product.id,
        'quantity': 2
    }

    touched_at = CartItemService.add_item_cart(
        cart=cart,
        item_data=item_data
    )

    assert CartItem.objects.filter(cart=cart, product=product).exists()
    assert touched_at is not None


@pytest.mark.django_db
def test_delete_item_cart_removes_item(cart, product):
    CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=1
    )

    item_data = {'id': product.id}

    touched_at = CartItemService.delete_item_cart(
        cart=cart,
        item_data=item_data
    )

    assert not CartItem.objects.filter(cart=cart, product=product).exists()
    assert touched_at is not None
