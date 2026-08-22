import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import connection

from products.models.brand import Brand
from products.models.category import Category
from products.models.product import Product
from products.models.subcategory import Subcategory

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


MODEL_CONFIG = {
    'product': {
        'model': Product,
        'create_url': 'api_products',
        'detail_url': 'api_products_detail',
        'test_list': [
            'TestSlugFieldMixins',
            'TestProductModel',
            'TestProductAPI',
        ]
    },
    'category': {
        'model': Category,
        'create_url': 'api_categories',
        'detail_url': 'api_categories_detail',
        'test_list': [
            'TestCatalogAPI', 
            'TestProtectDefaultMixin', 
            'TestSlugFieldMixins', 
            'TestFileCleanupMixin',
        ]
    },
    'subcategory': {
        'model': Subcategory,
        'create_url': 'api_subcategories',
        'detail_url': 'api_subcategories_detail',
        'test_list': [
            'TestCatalogAPI', 
            'TestSubcategoryAPI', 
            'TestSlugFieldMixins', 
            'TestFileCleanupMixin',
            'TestSubcategoryIntegrity',
        ]
    },
    'brand': {
        'model': Brand,
        'create_url': 'api_brands',
        'detail_url': 'api_brands_detail',
        'test_list': [
            'TestCatalogAPI', 
            'TestProtectDefaultMixin', 
            'TestSlugFieldMixins', 
            'TestFileCleanupMixin',
        ]
    }
}


MODEL_PARAMS = ['category', 'brand', 'subcategory', 'product']
# recorre en un for los params para cambiar las config y probar todos los modelos
@pytest.mark.django_db        
@pytest.mark.parametrize("model_key", MODEL_PARAMS, ids=[f"MODEL={m.upper()}" for m in MODEL_PARAMS])  
class BaseCatalogTest:
    
    @pytest.fixture(autouse=True)
    def separator(self, model_key, request):
        # request.node.name contiene el nombre de la función de test
        test_name = request.node.name
        class_name = request.cls.__name__ if request.cls else "Standalone"
        
        print("\n" + "="*50)
        print(f">>> TESTING MIXINS FOR: {class_name} <<<")    # poner el nombre de la clase hija ?
        # print(f">>> TESTING MIXINS FOR: {model_key.upper()} <<<")
        print(f"RUNNING: {test_name}")
        print("-"*50)
        yield
        
    @pytest.fixture(autouse=True)
    def _prepare(self, model_key):
        self.key = model_key
        self.model = MODEL_CONFIG[self.key]['model']
        
    @pytest.fixture(autouse=True)
    def _only_available_tests(self, request, model_key):
        # sirve para skipear tests
        class_name = request.cls.__name__ if request.cls else "Standalone"
        test_list = MODEL_CONFIG.get(model_key, {}).get('test_list', [])
        
        # para skipear otros modelos
        if class_name not in test_list:
            pytest.skip(f"[{model_key.upper()}] No puede ejecutar el test")
        
    
    @pytest.fixture
    def test_model(self, model_key) -> Category | Subcategory | Brand:
        # Lógica específica para Subcategoría (necesita una Categoría padre)
        if model_key == 'subcategory':
            parent, _ = Category.objects.get_or_create(
                name='Parent Test', 
                defaults={'slug': 'parent-test'}
            )
            return self.model.objects.create(
                name='Test Model', 
                slug='test-model', 
                category=parent
            )
        return self.model.objects.create(name='Test Model', slug='test-model')
    
    @property
    def show_db(self):
        # solo funciona dentro de django assertions
        for query in connection.queries:
            print(f"\nSQL: {query['sql']}\n")


class BaseCatalogAPITest(BaseCatalogTest):
    
    @pytest.fixture(autouse=True)
    def _prepare_api(self, model_key, test_model) -> Category | Subcategory | Brand:
        # URL para POST or GET LIST (Creación) 
        self.post_url = reverse(MODEL_CONFIG[model_key]['create_url'])
        # URL para GET, PATCH, DELETE (Detalle).
        self.detail_url = reverse(MODEL_CONFIG[model_key]['detail_url'], kwargs={'pk': test_model.id})
        
    def get_detail_url(self, model: Category | Subcategory | Brand) -> str:
        """URL custom para GET, PATCH, DELETE (Detalle)."""
        return reverse(MODEL_CONFIG[self.key]['detail_url'], kwargs={'pk': model.id})
    
    def get_detail_url_with_id(self, model_id: int | str) -> str:
        """URL custom para GET, PATCH, DELETE (Detalle)."""
        return reverse(MODEL_CONFIG[self.key]['detail_url'], kwargs={'pk': model_id})