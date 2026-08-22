import pytest
import logging
from django.test import utils
from django.db import IntegrityError, connection
from rest_framework import serializers
logger = logging.getLogger(__name__)

from rest_framework import status

from products.tests.conftest import BaseCatalogAPITest
from products.models.category import Category

  
class TestCatalogAPI(BaseCatalogAPITest):
    
    def test_hits_get(self, auth_client, test_model, django_assert_num_queries):
        with django_assert_num_queries(1):
            response = auth_client.get(self.post_url)
            
        with django_assert_num_queries(1):
            response = auth_client.get(self.get_detail_url(test_model))
            
            
    def test_create_model_success(self, model_key, auth_client, django_assert_num_queries, test_model):
        # Prueba la creación exitosa (POST).
        payload = {
            "name": "New Item Test",
            "image_url": "http://test.com/img.jpg"
        }
        
        # Si es subcategoría, necesitamos enviar el ID de la categoría padre
        if model_key == 'subcategory':
            parent = Category.objects.create(name="Parent-Post", slug="parent-post")
            
            with django_assert_num_queries(4):
                payload["category"] = parent.id
                # + 2 Query transaction atomic en el save de la subcaegory
                # 1 Query Buscar Category + 1 Query buscar Crear Subcategory
                response = auth_client.post(self.post_url, payload, format='json')
                self.show_db
                
        else:
            with django_assert_num_queries(1):
                response = auth_client.post(self.post_url, payload, format='json')
                for query in connection.queries:
                    print(f"\nSQL: {query['sql']}\n")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        
        # Verificamos que se creó en la DB
        assert self.model.objects.filter(name="New Item Test").exists()


    def test_duplicate_name_error(self, model_key, auth_client):
        if model_key == 'subcategory':
            # le doy de padre la por defecto a la subcategoría
            payload = {"name": "Repetido", 'category': 1}
        else:
            payload = {"name": "Repetido"}
            
        # Primer registro
        resp = auth_client.post(self.post_url, payload, format='json')
        assert resp.status_code == status.HTTP_201_CREATED
        
        # Segundo registro (Debería fallar por la DB, pero el serializer captura el error)
        response = auth_client.post(self.post_url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        print(response.data)
    
    def test_patch_model_optimized_update(self, model_key, auth_client, test_model, django_assert_num_queries):
        # Prueba la actualización parcial (PATCH). 
        if model_key == 'subcategory':
            pytest.skip("...")
            
        old_slug = test_model.slug
        new_name = "Updated Name"
        payload = {"name": new_name}
        
        model_id: int = test_model.id
        with django_assert_num_queries(4):
            # 1 Query inicia transaction
            # 1 Query para buscar + 1 Query para actualizar
            # 1 Query termina transaction
            response = auth_client.patch(self.get_detail_url_with_id(model_id), payload, format='json')
            self.show_db
        
        assert response.status_code == status.HTTP_200_OK
        
        # Recargamos de la DB para ver cambios
        test_model.refresh_from_db()
        assert test_model.name == new_name
        assert test_model.slug != old_slug  # El slug debería haber cambiado por el nombre nuevo

    def test_patch_delete_images_flag(self, model_key, auth_client, test_model):
        # Prueba que el flag delete_images setee image_url en None.
        # Primero nos aseguramos que tenga una imagen
        test_model.image_url = "original.jpg"
        test_model.save()
        
        payload = {"delete_images": 'true'}    
        response = auth_client.patch(self.detail_url, payload, format='json')
        print(response.data)
        test_model.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert test_model.image_url is None
        
        
    def test_patch_delete_early_check_defautl(self, model_key, auth_client, test_model):
        if model_key == 'subcategory':
            pytest.skip("...")
        
        default = self.model.objects.filter(is_default=True).first()
        default.image_url = "original.jpg"
        payload = {"delete_images": True}  
        response = auth_client.patch(self.get_detail_url_with_id(default.id), payload, format='json')
        print(response.data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
