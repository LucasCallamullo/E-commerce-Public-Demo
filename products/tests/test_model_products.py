# docker-compose exec web_client_1 pytest products/tests/test_model_products.py -s
import pytest
import logging
from django.test import utils
from django.db import IntegrityError
logger = logging.getLogger(__name__)

from products.tests.conftest import BaseCatalogTest
from products.models.product import Product
from products.models.subcategory import Subcategory
from products.models.category import Category
from products.models.brand import Brand


class TestProductModel(BaseCatalogTest):

    
    @pytest.fixture
    def get_models_defaults(self) -> dict:
        return {
            'category': Category.objects.filter(is_default=True).first(),
            'brand': Brand.objects.filter(is_default=True).first()
        }
        
    @pytest.fixture
    def setup_data(self):
        cat, _ = Category.objects.get_or_create(name="Test Cat")
        # su padre es la default
        sub, _ = Subcategory.objects.get_or_create(name="Test Sub")
        br, _ = Brand.objects.get_or_create(name="Test Brand")
        
        # category y brand son defaults
        prod, _ = Product.objects.get_or_create(name="Producto Test", subcategory=sub)
        return {
            'product': prod,
            'subcategory': sub,
            'category': cat,
            'brand': br,
        }
    
        # self.print_data(data=p1.__dict__, obj='Product Create')

    @pytest.fixture
    def get_setup_product(self, setup_data):
        return (
            Product.objects.filter(name="Producto Test")
            .select_related('category', 'subcategory')
            .only(
                'id', 'category_id', 'subcategory_id',
                'category__id', 
                'subcategory__id', 'subcategory__category_id')
            .first()
        )
        
    def test_product_on_change_parents_subcategory(self, setup_data, django_assert_num_queries):
        # su category es la default
        prod = setup_data['product']
        subcat_parent_def = setup_data['subcategory']
        cat = setup_data['category']
        
        self.print_data(subcat_parent_def.__dict__, 'Subcategory Default')
        
        with django_assert_num_queries(4):
            # + 2 Query transaction atomic en save de subcategory
            # 1 Query Guardar
            # + 1 Query Actualizar productos category in bulk
            subcat_parent_def.category = cat
            subcat_parent_def.save()
            self.print_data(subcat_parent_def.__dict__, 'Subcategory POST SAVE')
            self.show_db
        
        prod.refresh_from_db()
        
        assert prod.category == cat
        assert prod.subcategory == subcat_parent_def
       
    def test_product_on_delete_categories(self, get_models_defaults, setup_data, django_assert_num_queries):
        cat_def = get_models_defaults['category']
        
        category = setup_data['category']
        subcategory, _ = Subcategory.objects.get_or_create(name="Child Cat", category=category)
        # brand = setup_data['brand']
        
        product = setup_data['product']
        # Test de Save directo
        with django_assert_num_queries(1): 
            product.category = category
            product.subcategory = subcategory
            product.save()
        
        category.delete()
        subcategory.delete()
        
        product.refresh_from_db()
        assert product.category == cat_def
        assert product.subcategory == None
        
        
    def test_create_success_queries(self, get_models_defaults, setup_data, django_assert_num_queries):
        cat_def = get_models_defaults['category']
        brand = setup_data['brand']
        sub_child_cat_def = setup_data['subcategory']
        
        # Test de Create directo
        with django_assert_num_queries(1): 
            # 1 Query del create
            Product.objects.create(
                name="Product Valid",
                category=cat_def,  
                subcategory=sub_child_cat_def,
                brand=brand
            )
            self.show_db
        
        prod = Product.objects.filter(name="Product Valid").first()
        # testing save slugMixin
        assert prod.name == "Product Valid"
        assert prod.slug == "product-valid"
        assert prod.normalized_name == "product valid"

    def test_raise_integrity_error_on_inconsistent_category(self, setup_data, django_assert_num_queries):
        """Prueba que el save() lanza IntegrityError si la subcategoría no pertenece a la categoría."""
        # category no default
        other_cat = setup_data['category']
        subcat_parent_def = setup_data['subcategory']
        
        # Intentamos asignar subcat_parent_def junto con other_cat (no es el padre de la sub)
        product = Product(
            name="Invalid Product",
            category=other_cat,  
            subcategory=subcat_parent_def
        )
        self.print_data(data=product.__dict__, obj='Product Memory')

        # Atrapamos el raise especificando la excepción
        with django_assert_num_queries(0):
            # Dato cuando instancias modelo y despues llamas a save, realmente 
            # primero llama a su save, que tira el raise, por eso no busca la brand por defecto
            with pytest.raises(IntegrityError) as excinfo:
                product.save()
            self.show_db

        # Verificamos que el mensaje del error sea el que definimos en el modelo
        assert "is not a child of Category" in str(excinfo.value)
        
        # Test de Create directo
        with django_assert_num_queries(1): 
            # SQL: SELECT "products_brand"."id" AS "id" FROM "products_brand" 
            # WHERE "products_brand"."is_default" 
            # ORDER BY "products_brand"."id" ASC LIMIT 1
            # 1 Query de busqueda de la brand por defecto
            with pytest.raises(IntegrityError) as excinfo:
                Product.objects.create(
                    name="Invalid Producttt",
                    category=other_cat,  
                    subcategory=subcat_parent_def
                )
            self.show_db
        
        assert "is not a child of Category" in str(excinfo.value)
        
    
    def test_create_product_cases(self, get_models_defaults, django_assert_num_queries):
        cat_def = get_models_defaults['category']
        brand_def = get_models_defaults['brand']
        
        with django_assert_num_queries(3):
            # 1 Query busca Brand Default
            # 1 Query busca Category Default
            # 1 Query para crear
            p1 = Product.objects.create(name="Consola Uno Test")
            # self.print_data(data=p1.__dict__, obj='Product Create')
        
        # testeamos mixin
        assert p1.slug == 'consola-uno-test'
        assert p1.category == cat_def
        assert p1.brand == brand_def
        
        cat = Category.objects.create(name="Test Cat")
        with django_assert_num_queries(2):
            # 1 Query busca Brand Default
            # 1 Query para crear
            p1 = Product.objects.create(name="Consola Dos Test", category=cat)
            # self.print_data(data=p1.__dict__, obj='Product Create')
            
        assert p1.slug == 'consola-dos-test'
        assert p1.category == cat
        assert p1.brand == brand_def
            
        brand = Brand.objects.create(name="Test Brand")
        with django_assert_num_queries(1):
            # 1 Query para crear
            p1 = Product.objects.create(name="Consola Tres Test", category=cat, brand=brand)
            # self.print_data(data=p1.__dict__, obj='Product Create')
        
        assert p1.slug == 'consola-tres-test'
        assert p1.category == cat
        assert p1.brand == brand
        
        
    def test_selected_related(self, get_setup_product, django_assert_num_queries):
        with django_assert_num_queries(1): 
            p2 = (
                Product.objects.filter(name="Producto Test")
                .select_related('category', 'subcategory')
                .only(
                    'id', 'category_id', 'subcategory_id',
                    'category__id', 
                    'subcategory__id', 'subcategory__category_id')
                .first()
            )
            self.print_data(data=p2.category.__dict__, obj='Category Selected')
            
            if p2.__dict__.get('subcategory_id'):
                self.print_data(data=p2.subcategory.__dict__, obj='Subcategory Selected')
            
            self.print_data(data=p2.__dict__, obj=f'Product Filtered Only {p2.pk}')
        
            assert 'category_id' in p2.__dict__
            assert 'brand_id' not in p2.__dict__  
    
    
    def print_data(self, data:dict, obj: str):
        logger.info("\n===================== %s =======================================", obj)
        for key, value in data.items():
            logger.debug("Key %s | Value: %s", key, value)
        logger.info("============================================================")
        