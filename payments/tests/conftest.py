import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

# others apps
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

