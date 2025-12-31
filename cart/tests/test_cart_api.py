
import pytest
from rest_framework import status
from django.urls import reverse


@pytest.fixture
def cart_url(product):
    return reverse(
        'cart-api',  # nombre de tu path
        kwargs={'product_id': product.id}
    )
    
    
@pytest.mark.django_db
def test_add_product_success(api_client, cart_url):
    response = api_client.post(
        cart_url,
        {
            'action': 'add',
            'quantity': 2,
            'cart_quantity': 0
        },
        format='json'
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data['success'] is True
    assert response.data['detail'] == "Producto agregado."

    cart = response.data['cart']
    assert cart['total_quantity'] == 2
    assert len(cart['items']) == 1


@pytest.mark.django_db
def test_add_product_no_stock(api_client, cart_url):
    response = api_client.post(
        cart_url,
        {
            'action': 'add',
            'quantity': 50,
            'cart_quantity': 0
        },
        format='json'
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['success'] is False


@pytest.mark.django_db
def test_substract_product(api_client, cart_url):
    # add
    api_client.post(
        cart_url,
        {'action': 'add', 'quantity': 2},
        format='json'
    )

    # subtract
    response = api_client.post(
        cart_url,
        {'action': 'substract', 'quantity': 1},
        format='json'
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data['cart']['total_quantity'] == 1


@pytest.mark.django_db
def test_substract_product_not_in_cart(api_client, cart_url):
    response = api_client.post(
        cart_url,
        {'action': 'substract', 'quantity': 1},
        format='json'
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['success'] is False


@pytest.mark.django_db
def test_delete_product_success(api_client, cart_url, product):
    # PRIMERO: Agregar el producto al carrito
    add_response = api_client.post(
        cart_url,
        {
            'action': 'add',
            'quantity': 2,
            'cart_quantity': 0
        },
        format='json'
    )
    assert add_response.status_code == status.HTTP_200_OK
    
    # SEGUNDO: Eliminar el producto
    delete_response = api_client.delete(
        cart_url,
        {
            'action': 'delete'
        },
        format='json'
    )
    
    assert delete_response.status_code == status.HTTP_200_OK
    assert delete_response.data['success'] is True
    assert delete_response.data['detail'] == "Producto eliminado del carrito."
    
    # Verificar que el carrito quede vacío
    cart = delete_response.data['cart']
    assert cart['total_quantity'] == 0
    assert len(cart['items']) == 0