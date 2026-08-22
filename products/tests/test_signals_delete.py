
import pytest
from django.test import utils
from django.db import IntegrityError
from products.models.category import Category
from products.models.subcategory import Subcategory
from products.tests.conftest import BaseCatalogTest


class TestSubcategoryIntegrity(BaseCatalogTest):
    
    @pytest.fixture
    def setup_categories(self, db):
        """Prepara la categoría default y una categoría extra con subcategorías."""
        # La categoría default (is_default=True ya debería existir por tus fixtures o migraciones)
        # Si no, la creamos aquí.
        default_cat = Category.objects.filter(is_default=True).first()
        # Categoría que vamos a eliminar
        other_cat = Category.objects.create(name='Electronics', slug='electronics')
        
        return {
            'default': default_cat,
            'other': other_cat
        }

    def test_category_deletion_migrates_subcategories(self, setup_categories, django_assert_num_queries):
        """Escenario 1: Traslado simple sin colisión de nombres."""
        
        other_cat = setup_categories['other']
        default_cat = setup_categories['default']
        
        # Creamos una subcategoría en la categoría que va a morir
        sub = Subcategory.objects.create(name='Laptops', category=other_cat)
        
        # Acción: Borrar la categoría padre
        with django_assert_num_queries(7):
            # SQL: transaction init
            
            # SQL: SELECT "products_product"."id" FROM "products_product" WHERE "products_product"."category_id" IN (2)
            # NOTE 1 Query busca productos que tengan la Category Asociada y Setea la Default
            
            # SQL: SELECT "products_subcategory"."id", "products_subcategory"."name", "products_subcategory"."slug", 
            # "products_subcategory"."category_id", "products_category"."id", "products_category"."name", 
            # "products_category"."is_default" FROM "products_subcategory" INNER JOIN "products_category" 
            # ON ("products_subcategory"."category_id" = "products_category"."id") WHERE 
            # ("products_category"."is_default" OR "products_subcategory"."category_id" = 2)
            # NOTE 1 Query listado de subcategorías afectadas de la Category y las de Default Category
            
            # SQL: SELECT "products_category"."id" FROM "products_category" WHERE "products_category"."is_default" 
            # ORDER BY "products_category"."id" ASC LIMIT 1
            # NOTE 1 Query (OPCIONAL) En este caso ejecuta porque no hay categorías hijas en Default Category
            
            # SQL: UPDATE "products_subcategory" SET "category_id" = 1 WHERE "products_subcategory"."category_id" = 2
            # NOTE 1 Query (OPCIONAL) Si la categoría tenía hijas, ejecuta el bulk_update sobre las hijas
            
            # SQL: DELETE FROM "products_category" WHERE "products_category"."id" IN (2)
            # NOTE 1 Query delete la Category afectada
            
            # SQL: transaction init end
            other_cat.delete()
            self.show_db
        
        # Verificación: La subcategoría ahora pertenece a la default
        sub.refresh_from_db()
        assert sub.category == default_cat
        assert sub.name == 'Laptops' # El nombre se mantiene

    def test_category_deletion_resolves_collision(self, setup_categories, django_assert_num_queries):
        """Escenario 2: Traslado con colisión de nombres (mismo nombre en default)."""

        other_cat = setup_categories['other']
        default_cat = setup_categories['default']
        
        # Creamos subcategorías con el mismo nombre en ambas categorías
        Subcategory.objects.create(name='Others', category=default_cat)
        sub_to_move = Subcategory.objects.create(name='Others', category=other_cat)
        
        # Acción: Borrar la categoría padre
        # en este caso son 4 porque is_default tiene una hija entonces no hace falta buscarla
        with django_assert_num_queries(6):
            # el +2 queies es por los transaction atomic en el signal
            
            # SQL: SELECT "products_product"."id" FROM "products_product" WHERE "products_product"."category_id" IN (3)
            # NOTE 1 Query busca productos que tengan la Category Asociada y Setea la Default

            # SQL: SELECT "products_subcategory"."id", "products_subcategory"."name", "products_subcategory"."slug", 
            # "products_subcategory"."category_id", "products_category"."id", "products_category"."name", 
            # "products_category"."is_default" FROM "products_subcategory" INNER JOIN "products_category" 
            # ON ("products_subcategory"."category_id" = "products_category"."id") WHERE ("products_category"."is_default"
            # OR "products_subcategory"."category_id" = 3)
            # NOTE 1 Query listado de subcategorías afectadas de la Category y las de Default Category

            # SQL: UPDATE "products_subcategory" SET "name" = (CASE WHEN ("products_subcategory"."id" = 3) 
            # THEN 'Others (Electronics)' ELSE NULL END)::varchar(32), "slug" = (CASE WHEN ("products_subcategory"."id" = 3) 
            # THEN 'others-electronics' ELSE NULL END)::varchar(32), 
            # "category_id" = (CASE WHEN ("products_subcategory"."id" = 3) THEN 1 ELSE NULL END)::bigint 
            # WHERE "products_subcategory"."id" IN (3)
            # NOTE 1 Query (OPCIONAL) Si la categoría tenía hijas, ejecuta el bulk_update sobre las hijas
            
            # SQL: DELETE FROM "products_category" WHERE "products_category"."id" IN (3)
            # NOTE 1 Query delete la Category afectada
            other_cat.delete()
            self.show_db
        
        # Verificación: Se renombró para evitar el IntegrityError de la DB
        sub_to_move.refresh_from_db()
        expected_name = f"Others ({other_cat.name})"[:32]
        
        assert sub_to_move.category == default_cat
        assert sub_to_move.name == expected_name
        assert sub_to_move.slug != 'others' # El slug también debió cambiar

    def test_category_deletion_with_empty_subcategories_in_category(self, db, django_assert_num_queries):
        """Escenario 3: Traslado cuando la categoría default no tiene hijos."""
        
        other_cat = Category.objects.create(name='Old Cat')
        
        # Como este bloque no tiene subcategories hijas
        # solo dispara 1 query para buscar las subcategorias hijas asociadas
        # y + 1 Query por el delete + 1 Query por buscar productos con la category
        with django_assert_num_queries(5):    # + 2 es por transaction atomic en signal
            other_cat.delete()
        
        