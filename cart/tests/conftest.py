import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from products.models.product import Product
from cart.models import Cart

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@test.com",
        password="1234"
    )


@pytest.fixture
def cart(db, user):
    return Cart.objects.create(user=user)


@pytest.fixture
def product(db):
    return Product.objects.create(
        name="Producto test",
        slug="producto-test",
        price=100,
        stock=10,
        available=True
    )
    