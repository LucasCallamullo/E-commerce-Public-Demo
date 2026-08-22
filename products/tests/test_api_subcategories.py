import pytest
from rest_framework import status

from products.tests.conftest import BaseCatalogAPITest
from products.models.category import Category
from products.models.subcategory import Subcategory


class TestSubcategoryAPI(BaseCatalogAPITest):

    
    @pytest.fixture
    def extra_categories(self):
        """Crea categorías adicionales para pruebas de validación."""
        return {
            'normal': Category.objects.create(name="Normal Cat", slug="normal-cat"),
            'default': Category.objects.filter(is_default=True).first(),
        }
    
    def test_create_subcategory_success(self, auth_client, extra_categories, django_assert_num_queries):
        """POST: Creación exitosa vinculando a una categoría válida."""
        payload = {
            "name": "New Sub",
            "category": str(extra_categories['normal'].id)  # Enviamos el ID como string (CharField)
        }
        with django_assert_num_queries(4):
            # 1 query buscar la category
            # 1 query save la subcategory
            # +2 query transaction en el save de la subcategory
            
            response = auth_client.post(self.post_url, payload, format='json')
        
            assert response.status_code == status.HTTP_201_CREATED
            # Verificar que el to_representation devolvió el nombre de la categoría
            # print(response.data)
            assert response.data.get('subcategory', {}).get("category", {}).get('name') == "Normal Cat"
            assert response.data.get('subcategory', {}).get("category", {}).get('id') == extra_categories['normal'].id
        
        # Verificamos en DB
        new_sub = Subcategory.objects.get(name="New Sub")
        assert new_sub.category_id == extra_categories['normal'].id
        assert new_sub.slug == "new-sub"
    
    def test_update_subcategory_change_category(
        self, auth_client, test_model, extra_categories, django_assert_num_queries):
        """PATCH: Cambiar la subcategoría a una nueva categoría válida."""
        payload = {"category": extra_categories['normal'].id}
        
        with django_assert_num_queries(8):
            # + 2 Query en atomic en el save de la subcategory
            # 1 Query obtener Subcategory + 1 Query Get New Category + 1 Save Subcategory
            # + 1 Query para actualizar productos si los tuviera
            response = auth_client.patch(self.get_detail_url(test_model), payload, format='json')
            self.show_db
        
        assert response.status_code == status.HTTP_200_OK
        test_model.refresh_from_db()
        assert test_model.category == extra_categories['normal']
    
    
    def test_error_duplicate_name_in_category(self, auth_client, test_model, extra_categories):
        # forzar error de integridad en la respuesta
        # por defecto se asigna la default si no decimos nada
        sub_parent_default = self.model.objects.create(name='Test Model')
        assert sub_parent_default.slug == 'test-model'
        assert sub_parent_default.category == extra_categories['default']

        payload = {"category": str(extra_categories['default'].id)}
        response = auth_client.patch(self.get_detail_url(test_model), payload, format='json')
        # tira error por repetir nombres/slug dentro de la misma categoría 
        print(response.data)
    
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # test_model.refresh_from_db()
        assert test_model.category.slug == 'parent-test'    # no changes


    def test_error_invalid_category_id_and_assign_default(self, auth_client, test_model, extra_categories):
        """Error: Enviar un ID que no es un UUID/ID válido o no existe."""
        # ID inexistente
        payload = {"category": "99999"} 
        response = auth_client.patch(self.get_detail_url(test_model), payload, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # asigna la category por defecto
        test_model.refresh_from_db()
        assert test_model.category == extra_categories['default']

    def test_update_name_and_category_simultaneously(self, auth_client, test_model, extra_categories):
        """PATCH: Cambiar nombre y categoría al mismo tiempo sin conflictos."""
        
        new_name = "Unique Name In New Cat"
        payload = {
            "name": new_name,
            "category": str(extra_categories['normal'].id)
        }
        response = auth_client.patch(self.detail_url, payload, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        test_model.refresh_from_db()
        assert test_model.name == new_name
        assert test_model.category == extra_categories['normal']