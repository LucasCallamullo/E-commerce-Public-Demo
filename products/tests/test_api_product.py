from decimal import Decimal
import pytest
import logging

from django.test import utils
from django.db import IntegrityError, connection
from rest_framework import serializers


logger = logging.getLogger(__name__)

from rest_framework import status

from products.tests.conftest import BaseCatalogAPITest

from products.models.product import Product
from products.models.product_image import ProductImage
from products.models.category import Category
from products.models.subcategory import Subcategory
from products.models.brand import Brand

  
class TestProductAPI(BaseCatalogAPITest):
    
    @pytest.fixture
    def get_setup_catalog(self):
        a, _ = Category.objects.get_or_create(name='Cat Test')
        b, _ = Subcategory.objects.get_or_create(category=a, name='Subcat Test')
        c, _ = Brand.objects.get_or_create(name='Brand Test')
        
        # this product has default Category and Brand, and Subcategory is None
        d, _ = Product.objects.get_or_create(name='Product Test', price_ars='1500', price_usd='1')
        
        return {
            'cat_def': Category.objects.filter(is_default=True).first(),
            'br_def': Brand.objects.filter(is_default=True).first(),
            'cat_test': a,
            'sub_test': b,
            'br_test': c,
            'prod_def': d,
        }
        
    def test_linked_pricing(self, auth_client, get_setup_catalog):
        product = get_setup_catalog['prod_def']
        # request step
        payload = {
            # 'stock_increment': 5,
            'is_linked_prices': True,
            'price_ars': '2800',
        }
        response = auth_client.patch(self.get_detail_url(model=product), payload, format='json')
        assert response.status_code == 200
        logger.debug("%s", response.data)  
        
        product.refresh_from_db()
        # valores originales price_ars = '1500' y price_usd '1'
        assert product.price_ars == Decimal('2800')
        assert product.price_usd == Decimal('2')
        
        
    def test_linked_pricing_no_changes(self, auth_client, get_setup_catalog):
        product = get_setup_catalog['prod_def']
        # request step
        payload = {
            # 'stock_increment': 5,
            'is_linked_prices': True,
        }
        response = auth_client.patch(self.get_detail_url(model=product), payload, format='json')
        assert response.status_code == 200
        logger.debug("%s", response.data)  
        
        product.refresh_from_db()
        # valores originales price_ars = '1500' y price_usd '1'
        assert product.price_ars == Decimal('1500')
        assert product.price_usd == Decimal('1')
        
        
    def test_linked_pricing_false(self, auth_client, get_setup_catalog):
        # asumimos que el usd es este valor de '1400'
        # aunque podriamos traerlo del service de momento lo hardcoderamos para evitar 
        # dependencias cruzadas
        product = get_setup_catalog['prod_def']
        # request step
        payload = {
            'is_linked_prices': False,
            'price_ars': '2000',
        }
        response = auth_client.patch(self.get_detail_url(model=product), payload, format='json')
        assert response.status_code == 200
        logger.debug("%s", response.data)  
        
        product.refresh_from_db()
        # valores originales price_ars = '1500' y price_usd '1'
        assert product.price_ars == Decimal('2000')
        assert product.price_usd == Decimal('1')
        
        
    def test_cost_and_stock_related(self, auth_client, get_setup_catalog):
        product = get_setup_catalog['prod_def']
        # request step
        payload = {
            # 'stock_increment': 5,
            'cost_unit': '1200',
        }
        response = auth_client.patch(self.get_detail_url(model=product), payload, format='json')
        assert response.status_code == 400
        logger.debug("%s", response.data)
        
    
    def test_cost_avg_patch(self, auth_client, get_setup_catalog):
        # Setup inicial
        current_stock = 10
        current_cost = Decimal('1000')
        product = Product.objects.create(
            name='Product On Test', 
            price_ars='1500', 
            cost_avg_ars=current_cost, 
            stock=current_stock
        )
        # request step
        payload = {
            'stock_increment': 5,
            'cost_unit': '1200',
        }
        response = auth_client.patch(self.get_detail_url(model=product), payload, format='json')
        assert response.status_code == 200
        
        # Cálculo esperado (usando la misma lógica que el Service)
        new_qty = 5
        new_cost_unit = Decimal('1200')
        
        expected_stock = current_stock + new_qty
        expected_avg_cost = ((current_cost * current_stock) + (new_cost_unit * new_qty)) / expected_stock
        # Aplicamos el redondeo del Service para que el assert no falle por decimales
        expected_avg_cost = expected_avg_cost.quantize(Decimal('0.01'))

        # Verificación
        product.refresh_from_db()
        er_msg = f"WAC fallido: esperado {expected_avg_cost}, obtenido {product.cost_avg_ars}"
        assert product.stock == expected_stock, "El stock total no se actualizó correctamente"
        assert product.cost_avg_ars == expected_avg_cost, er_msg
        
    
    def test_max_qeuries_on_patch(self, auth_client, get_setup_catalog, django_assert_max_num_queries):
        # Test de qeuries  y ejecucion de todos los casos juntois
        
        # category y brand default por defecto y stock = 0
        product = Product.objects.create(name='Product On Test', price_ars='50', main_image='http//example.com')
        
        img1 = ProductImage.objects.create(product=product, main_image=True, image_url='http//example.com')    
        img2 = ProductImage.objects.create(product=product, main_image=False, image_url='http//other.com')    
        
        payload = {
            "name": "New Item Test",
            'category': get_setup_catalog['cat_test'].id,
            'subcategory': get_setup_catalog['sub_test'].id,
            'brand': get_setup_catalog['br_test'].id,
            'stock_increment': 5,
            'cost_unit': '1000',
            'main_image': img2.id,
        }
        
        with django_assert_max_num_queries(11):
            # + 1 Query get Product for update
            # + 1 Query (Optional) Get new Category or not
            # + 1 Query (Optional) Get new Subategory or not
            # + 1 Query (Optional) Get new Brand or not
            # + 1 Query Inicio de transaction
            # + 1 Query (Optional) Get todas las imagenes asociadas al Producto y verificar el nuevo id
            # + 1 Query (Optional) Actualizar imagenes y demotear en una sola Consulta
            # + 1 Query updated atomic solo los campos que realmente cambiaron
            # + 1 Query Create PriceHistory Model 
            # + 1 Query Create AuditLog Model
            # + 1 Query Cierre de transaction 
            response = auth_client.patch(self.get_detail_url(model=product), payload, format='json')
            
            print(response.data)
            assert response.status_code == status.HTTP_200_OK
            # self.show_db
            
        product.refresh_from_db()  
        
        assert product.category_id == get_setup_catalog['cat_test'].id
        assert product.subcategory_id == get_setup_catalog['sub_test'].id
        assert product.brand_id == get_setup_catalog['br_test'].id
        assert product.stock == 5
        assert product.cost_avg_ars == Decimal('1000')
        assert product.main_image == 'http//other.com'
        
    def test_inconsistency_categories(self, auth_client, get_setup_catalog): 
        # category Defautl ,Subcategory None   
        product: Product = get_setup_catalog['prod_def']
        
        # parent category Test
        sub = get_setup_catalog['sub_test']
        
        # request step
        payload = {
            'subcategory': sub.id,
        }
        
        # inconsistencia 
        response = auth_client.patch(self.get_detail_url(model=product), payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        product.refresh_from_db()
        
        assert product.category_id == get_setup_catalog['cat_def'].id
        assert product.subcategory_id == None  
        
      
    def test_set_category_default_and_subcategory_none(self, auth_client, get_setup_catalog): 
        
        cat = get_setup_catalog['cat_test']
        sub = get_setup_catalog['sub_test'] # parent category Test
        product = Product.objects.create(name='some', price_ars='1000', category=cat, subcategory=sub)
        
        # request step
        # this reset category to default and subcategory to None
        # if you dont send someone this response 400 for inconsistency
        payload = {
            'category': 0,
            'subcategory': 0,
        }
        
        response = auth_client.patch(self.get_detail_url(model=product), payload, format='json')
        assert response.status_code == 200
        
        product.refresh_from_db()
        
        assert product.category_id == get_setup_catalog['cat_def'].id
        assert product.subcategory_id == None        
        
        
    def test_only_set_category_default(self, auth_client, get_setup_catalog): 
        
        cat = get_setup_catalog['cat_test']
        sub = get_setup_catalog['sub_test'] # parent category Test
        product = Product.objects.create(name='some', price_ars='1000', category=cat, subcategory=sub)
        
        # request step
        # this reset category to default and subcategory to None
        # if you dont send someone this response 400 for inconsistency
        payload = {
            'category': 0,
            # 'subcategory': 0,
        }
        
        response = auth_client.patch(self.get_detail_url(model=product), payload, format='json')
        assert response.status_code == 400
        
        product.refresh_from_db()
        
        # assert product.category_id == get_setup_catalog['cat_def'].id
        assert product.category_id == get_setup_catalog['cat_test'].id
        assert product.subcategory_id == get_setup_catalog['sub_test'].id        
        