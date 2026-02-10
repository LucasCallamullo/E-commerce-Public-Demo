import pytest
from django.urls import reverse
from home.models import Store, StoreImage


@pytest.mark.django_db
class TestStoreImageAPI:
    
    @pytest.fixture
    def url_list(self, store_data):
        """URL para POST (lista/creación)"""
        return reverse('api_store_images', kwargs={'store_id': store_data.id})

    @pytest.fixture
    def url_detail(self, store_data, initial_image):
        """URL para PATCH (detalle)"""
        return reverse('api_store_images_detail', kwargs={
            'store_id': store_data.id, 
            'image_id': initial_image.id
        })
    
    # --- TESTS POST (Creación) ---

    def test_create_image_success(self, auth_client, store_data, url_list):
        data = {
            "image_type": "header",
            "image_url": "https://img.com/1.jpg",
            "main_image": False,
            "available": True
        }
        response = auth_client.post(url_list, data, format='json')
        
        assert response.status_code == 201
        assert response.data['success'] is True
        assert StoreImage.objects.filter(image_url="https://img.com/1.jpg").exists()


    def test_create_main_image_demotes_previous(self, auth_client, store_data, initial_image, url_list):
        """Si creo una nueva MAIN, la anterior debe dejar de serlo automáticamente."""
        
        data = {
            "image_type": "header",
            "image_url": "https://img.com/new-main.jpg",
            "main_image": True, # Nueva principal
            "available": True
        }
        auth_client.post(url_list, data, format='json')
        
        # Verificamos
        initial_image.refresh_from_db()
        assert initial_image.main_image is False # La vieja ya no es main
        assert StoreImage.objects.get(image_url="https://img.com/new-main.jpg").main_image is True


    def test_error_main_and_not_available(self, auth_client, store_data, url_list):
        """Error si intento crear una principal que está oculta."""
        data = {
            "image_type": "header",
            "image_url": "https://img.com/new-main.jpg",
            "main_image": True,
            "available": False
        }
        response = auth_client.post(url_list, data, format='json')
        
        assert response.status_code == 400
        assert "No se puede marcar como Imagen Principal si está oculta" in str(response.data)

    # --- TESTS PATCH (Actualización) ---

    def test_patch_image_url_only(self, auth_client, store_data, initial_image, url_detail):
        """Prueba que el partial=True funcione (enviar solo un campo)."""

        data = {"image_url": "https://new-url.com/update.jpg"}
        
        response = auth_client.patch(url_detail, data, format='json')
        
        assert response.status_code == 200
        initial_image.refresh_from_db()
        
        assert initial_image.image_url == "https://new-url.com/update.jpg"
        assert initial_image.image_type == "header" # Se mantuvo igual
        assert initial_image.main_image == True # Se mantuvo igual
        assert initial_image.available == True # Se mantuvo igual


    def test_error_hide_last_available_image(self, auth_client, store_data, initial_image, url_detail):
        """Regla de negocio: No puedo ocultar la única imagen disponible del tipo."""
        data = {"available": False} # Intentamos ocultar la única que hay
        
        response = auth_client.patch(url_detail, data, format='json')
        
        assert response.status_code == 400
        assert "No se puede marcar como Imagen Principal si está oculta" in str(response.data)
        
        
    def test_error_patch_image_from_different_store(self, auth_client, store_data):
        """Error 404: Intentar editar una imagen que existe, pero pertenece a otra tienda."""
        
        # 1. Creamos otra tienda y su imagen
        other_store = Store.objects.create(name="Other Store")
        other_image = StoreImage.objects.create(
            store=other_store, 
            image_type='header', 
            image_url="https://new-url.com/update.jpg"
        )

        # 2. Intentamos acceder vía la tienda original (store_data)
        url = reverse('api_store_images_detail', kwargs={
            'store_id': store_data.id, 
            'image_id': other_image.id
        })
        
        response = auth_client.patch(url, {"available": False}, format='json')

        # 3. Verificaciones
        assert response.status_code == 404
        # Si quieres ser detallista con el mensaje:
        assert "Store Image not found" in str(response.data)