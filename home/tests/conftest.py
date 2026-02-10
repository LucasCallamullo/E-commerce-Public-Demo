import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from home.models import Store
from home.models import StoreImage

# others apps
User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin(db):
    return User.objects.create_user(
        email="admin@test.com",
        password="1234",
        role='admin'
    )
    
@pytest.fixture
def auth_client(api_client, admin):
    """Retorna un cliente autenticado como administrador."""
    api_client.force_authenticate(user=admin)
    return api_client
    
    
@pytest.fixture
def store_data(db):
    store, _ = Store.objects.get_or_create(
        name= "Cat Cat Games",
        wsp_number = "+54 9 351 543-7688",
        address = "Calle Falsa 123",
        cellphone = "351 543-7688",
        email = "cat_cat_games@gmail.com",
    )
    return store


@pytest.fixture
def initial_image(store_data):
    store = StoreImage.objects.create(
        store=store_data,
        image_type=StoreImage.ImageType.HEADER,
        image_url='https://example.com/initial.jpg',
        main_image=True,
        available=True
    )
    print("=" * 50)
    return store
    
    
