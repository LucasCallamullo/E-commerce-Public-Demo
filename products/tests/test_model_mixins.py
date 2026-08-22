# docker-compose exec web_client_1 pytest products/tests/test_mixins.py -s
import pytest
import logging
from django.test import utils
logger = logging.getLogger(__name__)

from products.tests.conftest import BaseCatalogTest
# class Category(FileCleanupMixin, SlugFieldMixin, ProtectDefaultMixin, models.Model):
# class Subcategory(FileCleanupMixin, SlugFieldMixin, models.Model):

class TestProtectDefaultMixin(BaseCatalogTest):
    def test_hits_is_default(self, model_key, django_assert_num_queries):
        if model_key == 'subcategory':
            pytest.skip("Subcategory no tiene protección de default")
            
        # Usamos el manager .objects
        with django_assert_num_queries(1):
            self.model.objects.create(name='Proofs', slug='proofs')
        
        with django_assert_num_queries(1):
            # Traemos el objeto limitado
            obj = self.model.objects.only('name').get(name='Proofs')
        
        # Verificamos que no está en el dict
        assert 'is_default' not in obj.__dict__
        
        # Como no hay is_default en __dict__, el Mixin dispara el getattr 
        # + el save() debería ser 2 hits
        with django_assert_num_queries(2):
            obj.save()
        
        with django_assert_num_queries(0):
            # Asignar NO dispara query
            # obj.is_default = True 
            # Leerlo ahora tampoco, porque ya lo asignamos
            current_val = obj.is_default
            print(f"DEFAULT: {obj.is_default}")
        
    def test_protect_mixin_logic(self, test_model, model_key, django_assert_num_queries):
        """Verifica que no se puede modificar una instancia protegida."""
        if model_key == 'subcategory':
            pytest.skip("Subcategory no tiene protección de default")

        # 1. Buscamos el default creado por el post_migrate
        model_class = test_model.__class__
        with django_assert_num_queries(1):
            default_obj = model_class.objects.get(is_default=True)
        
        # 2. Intentar guardar cambios debe fallar
        default_obj.name = "Nuevo Nombre"
        with pytest.raises(ValueError, match=default_obj.protected_message):
            default_obj.save()

        # 3. Intentar borrar debe fallar
        with pytest.raises(ValueError, match=default_obj.protected_message):
            default_obj.delete()
            
        # El Mixin debería saltar aquí al detectar el True
        # 1 hit GET  - 2 HIT getattr(is_default)   y raises
        with django_assert_num_queries(2):
            with pytest.raises(ValueError, match=self.model.protected_message):
                obj = self.model.objects.only('name').get(is_default=True)
                obj.save()

    def test_prevent_new_default_creation(self, model_key):
        """Verifica que el Mixin bloquea la creación de un SEGUNDO default."""
        if model_key == 'subcategory':
            pytest.skip("Subcategory no tiene protección de default")
        
        # Intentar crear un default nuevo (aunque sea el segundo)
        with pytest.raises(ValueError):
            self.model.objects.create(name="Otro Default", is_default=True)


class TestSlugFieldMixins(BaseCatalogTest):

    def test_zero_queries_on_init(self, test_model, django_assert_num_queries):
        """Verifica que el Mixin no haga SQL al inicializarse."""
        # Supongamos que test_model ya fue creado. Lo refrescamos de la DB 
        # usando .only() para simular un escenario de carga parcial.
        model_class = test_model.__class__
        
        with django_assert_num_queries(1):
            # 1 query para traer el objeto
            obj = model_class.objects.only('name').get(pk=test_model.pk)

        # Ahora verificamos que acceder a las propiedades del Mixin sea CERO queries
        with django_assert_num_queries(0):
            _ = obj._last_name      # Debería venir de __dict__
            logger.debug('_last_name: %s', obj._last_name)
            
            
    def test_slug_generated_on_creation(self, model_key):
        """Verifica que el slug se genera automáticamente al crear el objeto."""
        # Usamos el modelo de la iteración actual
        obj = self.model.objects.create(name="Producto de Prueba")
        assert obj.slug == "producto-de-prueba"

    def test_slug_updates_when_name_changes(self, model_key):
        """Verifica que el slug se actualiza si el nombre cambia."""
        obj = self.model.objects.create(name="Nombre Inicial")
        original_slug = obj.slug # nombre-inicial
        
        obj.name = "Nombre Nuevo"
        obj.save()
        # obj.refresh_from_db()
        assert obj.slug == "nombre-nuevo"
        assert obj.slug != original_slug

    def test_slug_does_not_update_if_name_is_same(self, model_key, django_assert_num_queries):
        """
        Optimización: Verifica que no se re-calcula el slug ni se altera 
        si el nombre no ha cambiado.
        """
        obj = self.model.objects.create(name="Mismo Nombre")
        
        # Simulamos un guardado sin cambios en el nombre
        obj.save()
        assert obj.slug == "mismo-nombre"

    def test_slug_persistence_with_update_fields(self, model_key):
        """
        Verifica que el Mixin inyecta el 'slug' en update_fields si el nombre cambió,
        evitando que el cambio de slug se pierda.
        """
        obj = self.model.objects.create(name="Original")
        
        obj.name = "Cambiado"
        # Forzamos update_fields solo con 'name'
        obj.save(update_fields=['name'])
        
        # Recargamos de la DB para ver si el slug realmente se guardó
        obj.refresh_from_db()
        assert obj.name == "Cambiado"
        assert obj.slug == "cambiado" # El Mixin debió inyectar 'slug' en el save

    def test_slug_generated_if_missing_on_creation(self, model_key):
        """Verifica que si enviamos un slug manual, el Mixin NO lo respeta.
        Lo registra basado en el nombre
        """
        obj = self.model.objects.create(name="Nombre", slug="slug-manual-personalizado")
        assert obj.slug != "slug-manual-personalizado"
        assert obj.slug == "nombre"
        
        
class TestFileCleanupMixin(BaseCatalogTest):
    
    def test_no_cleanup_on_new_instance(self, model_key):
        """Una instancia nueva (sin PK) nunca debe pedir cleanup."""
        # Creamos el objeto en memoria pero NO lo guardamos (sin PK)
        obj = self.model(name="New", image_url="test.jpg")
        assert obj.needs_cleanup_file is False

    def test_no_cleanup_when_image_is_same(self, model_key):
        """Si la imagen no cambia, no debe pedir cleanup."""
        obj = self.model.objects.create(name="Test", image_url="original.jpg")
        
        # Sigue siendo la misma
        assert obj.needs_cleanup_file is False
        
        obj.save()
        assert obj.needs_cleanup_file is False

    def test_detects_cleanup_when_image_changes(self, model_key):
        """Debe detectar el cambio cuando asignamos una nueva URL."""
        obj = self.model.objects.create(name="Test", image_url="old.jpg")
        
        obj.image_url = "new.jpg"
        
        # El mixin debe detectar que 'old.jpg' != 'new.jpg'
        assert obj.needs_cleanup_file is True
        assert obj.safe_original_url == "old.jpg"
        obj.save()

    def test_no_cleanup_if_original_was_empty(self, model_key):
        """Si no había imagen antes, no hay nada que limpiar."""
        obj = self.model.objects.create(name="Test", image_url=None) # O ""
        
        obj.image_url = "first_image.jpg"
        
        _ = obj._original_url   # Debería venir de __dict__
        logger.debug('_original_url: %s', obj._original_url)
        # Como _original_url era None/vacío, no hay cleanup del archivo anterior
        assert obj.needs_cleanup_file is False

    def test_performance_no_query_on_cleanup_check(self, model_key, django_assert_num_queries):
        """
        Prueba de fuego: Verificar que needs_cleanup_file NO dispara SQL 
        incluso si el campo image_url no fue cargado originalmente.
        """
        obj_base = self.model.objects.create(name="Test", image_url="photo.jpg")
        
        # Cargamos solo el nombre (deferred loading para image_url)
        obj = self.model.objects.only('name').get(pk=obj_base.pk)
        
        with django_assert_num_queries(0):
            # No debería hitear la DB porque usamos __dict__.get()
            result = obj.needs_cleanup_file
            assert result is False # Es False porque image_url no está en dict
