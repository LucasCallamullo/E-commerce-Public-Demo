"""
NOTES ON METHOD RESOLUTION ORDER (MRO) & EXECUTION FLOW
-------------------------------------------------------
Inheritance Order: (FileCleanupMixin, SlugFieldMixin, ProtectDefaultMixin, models.Model)

1. __init__ (STATE INITIALIZATION):
    - Upward: Calls propagate up to models.Model to instantiate the object with DB data.
    - Downward: On the way back, each Mixin captures its "initial state" into private 
      attributes (_original_url, _last_name) by safely accessing self.__dict__.

2. save() (TRANSFORMATION & VALIDATION):
    - SlugFieldMixin: Data transformation layer (generates slug in memory).
    - ProtectDefaultMixin: Integrity validation layer (can abort the process).
    - models.Model: Final persistence layer. Executes SQL only if all mixins permit.

3. delete() (SECURITY):
    - ProtectDefaultMixin: Intercepts the call to validate if the record is 
      deletable before allowing models.Model to execute the SQL DELETE command.
"""
from django.utils.text import slugify
from core.utils.utils_parsers import normalize_or_None
import logging
logger = logging.getLogger(__name__)


class FileCleanupMixin:
    """
    Mixin to track 'image_url' changes for physical file management.

    This mixin provides a shadow state of the original image URL, allowing 
    signals to determine if a previously stored file should be deleted from the 
    storage system (Cleanup).

    It is specifically designed to work with the logic defined in signals.py.
    """

    def __init__(self, *args, **kwargs):
        """
        Initializes the model and captures the original image_url state.

        To maintain high performance, it accesses __dict__ directly. This avoids 
        triggering 'Deferred Field Loading' (extra SQL queries) if the model was 
        fetched using .only() or .defer() excluding the 'image_url' field.
        """
        super().__init__(*args, **kwargs)
        
        # Store a snapshot of the URL as it exists in the database.
        self._original_url = self.__dict__.get('image_url')

    @property
    def safe_original_url(self) -> str | None:
        """
        Returns the initial URL snapshot without the risk of a database hit.
        """
        return self._original_url

    @safe_original_url.setter
    def safe_original_url(self, value: str | None):
        """
        Manually updates the shadow state of the URL.
        Useful for bulk operations or specialized synchronization tasks.
        """
        self._original_url = value

    @property
    def needs_cleanup_file(self) -> bool:
        """
        Determines if a previous physical file requires deletion.

        Returns:
            bool: True if a valid original URL exists and it differs from 
                  the current memory state (meaning the file path was updated).
        """
        # 1. Si no hay PK o no tenemos snapshot del original, no hay nada que limpiar
        if not self.pk or not self._original_url:
            logger.debug(
                "[FILE_MIXIN] not pk: %s or not self._original_url: %s", 
                self.pk, self._original_url
            )
            return False
        
        # 2. Obtenemos el valor actual de memoria SIN disparar SQL
        current_url = self.__dict__.get('image_url')
        logger.debug("[FILE_MIXIN] current_url: %s | _original_url: %s", current_url, self._original_url)
        
        # 3. Detects a path change.
        # logger.debug("[FILE_MIXIN][needs_cleanup_file] bool: %s", bool(self._original_url != current_url))
        return bool(self._original_url != current_url)


class SlugFieldMixin:
    """
    Mixin for automatic 'slug' field management based on the 'name' field.
    
    This Mixin optimizes performance by preventing additional SQL queries (Lazy Loading)
    when accessing model attributes during the instance lifecycle.
    
    Model Requirements:
        - name (CharField): The source field from which the slug is derived.
        - slug (SlugField): The destination field where the URL-friendly value is stored.
    """
    HAS_NORMALIZED_NAME = False

    def __init__(self, *args, **kwargs):
        """
        Captures the initial state of the name when the object is instantiated.
        
        Uses direct __dict__ access to avoid triggering Deferred (SQL) queries
        if the model was loaded using .only() or .defer().
        """
        super().__init__(*args, **kwargs)
        # _last_name acts as a 'snapshot' to detect changes within the save() method.
        self._last_name = self.__dict__.get('name')

    @staticmethod
    def get_new_slug(name: str) -> str:
        return slugify(name)

    def save(self, *args, **kwargs):
        """
        Orchestrates slug logic before persisting data to the database.
        
        Behaviors:
            1. Creation: If the object is new (pk is None) and has a name but no slug, 
               it generates one automatically.
            2. Update: If the name has changed relative to the initial snapshot (_last_name),
               it regenerates the slug.
            3. update_fields Integrity: If a partial save is performed, it ensures the 
               new slug is included in the final SQL query.
        """
        # Extract values from memory to avoid triggering Django Descriptors (SQL queries)
        name = self.__dict__.get('name')
        
        # Case A: New instance --> self.pk is None:
        # Case B: Existing instance (Update)
        # Compare current memory value against the __init__ snapshot
        if self.pk is None or (self._last_name and name != self._last_name):
            
            self.slug = slugify(name)
            
            if self.HAS_NORMALIZED_NAME:
                self.normalized_name = normalize_or_None(name)
            
            # 1. Si usaron update_fields, nos aseguramos de que el slug viaje a la DB
            if 'update_fields' in kwargs:
                logger.debug("[SLUG_MIXIN][SAVE on UPDATE][Step 1]: update_fields: %s", kwargs.get('update_fields'))
                
                # 2. Aseguramos que sea una lista para poder usar .append()
                fields = kwargs['update_fields']
                if not isinstance(fields, list):
                    fields = list(kwargs['update_fields'])
                
                if 'slug' not in fields:
                    # 3. Solo actualizamos kwargs si realmente tocamos la lista
                    fields.append('slug')
                    kwargs['update_fields'] = fields
                    
                if self.HAS_NORMALIZED_NAME and 'normalized_name' not in fields:
                    fields.append('normalized_name')
                    kwargs['update_fields'] = fields
                    
                logger.debug("[SLUG_MIXIN][SAVE on UPDATE][Step 2]: update_fields: %s", kwargs.get('update_fields'))

        return super().save(*args, **kwargs)


class ProtectDefaultMixin:
    """
    Mixin to prevent the creation, modification, or deletion of 'is_default' instances.

    This mixin ensures system integrity by making default records immutable and 
    preventing the accidental creation of additional default entries via standard 
    save operations.

    Model Requirements:
        - is_default (BooleanField): Flag indicating if the record is a protected default.
    """
    # User-facing message (kept in Spanish as per project requirements)
    protected_message = "No se puede crear, modificar o eliminar una instancia por defecto."

    def save(self, *args, **kwargs):
        """
        Enforces strict default instance protection.
        
        Logic:
            - If 'is_default' is True in memory (new or existing object), the save is blocked.
            - This prevents creating new defaults via Category.objects.create(is_default=True).
        """
        if self._get_real_default():
            logger.debug("[PROTECT_MIXIN][Raise protected_message | PK: %s", self.pk)
            raise ValueError(self.protected_message)

        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Prevents deletion of instances marked as default.
        """
        if self._get_real_default():
            logger.debug("[PROTECT_MIXIN][Raise protected_message | PK: %s", self.pk)
            raise ValueError(self.protected_message)

        super().delete(*args, **kwargs)

    def _get_real_default(self) -> bool:
        """
        Retrieves the 'is_default' status with a focus on strict integrity.
        
        Logic:
            1. Priority: Check __dict__ for the in-memory value. This catches 
               attempts to create new objects with is_default=True.
            2. Fallback: If the record exists (pk) but the field is missing from 
               memory (deferred), it fetches it from the DB to ensure protection.
        
        Returns:
            bool: True if the instance is marked as default, False otherwise.
        """
        # Step 1: Access __dict__ directly. 
        # If we are creating a new object: Category(is_default=True), 
        # the value will be here in memory.
        is_default = self.__dict__.get('is_default', None)
        # logger.debug("[PROTECT_MIXIN][STEP 1 - _get_real_default]: %s", is_default)
        
        # Step 2: If memory has nothing (None) AND the object exists in DB,
        # we must check the DB state to prevent updating a protected record.
        if is_default is None and self.pk:
            is_default = getattr(self, "is_default", False)
            # logger.debug("[PROTECT_MIXIN][STEP 2 - _get_real_default]: %s", is_default)
 
        return bool(is_default)
    
   

"""  
NOTE Como se ejecutan las llamadas del __init__ por si se olvidan 
--------------------------------------------------------------------------------------------------------
- Subida: FileCleanupMixin → SlugFieldMixin → models.Model.
- Carga: models.Model llena el __dict__ con los datos de la DB.
- Bajada: Se ejecutan las líneas de SlugFieldMixin (guarda _last_name) y finalmente las de 
    FileCleanupMixin (guarda _original_url).


NOTE EXAMPLE
--------------------------------------------------------------------------------------------------------
# En Python, el orden en que declaras las clases en la herencia define el Method Resolution Order (MRO).
# Por eso el orden de los save() o delete() primero llaman a ProtectDefaultMixin y después a models.Model
class Category(FileCleanupMixin, SlugFieldMixin, ProtectDefaultMixin, models.Model):


NOTE Como se ejecutan las llamadas del save() por si se olvidan 
--------------------------------------------------------------------------------------------------------
Llamada: category.save()
================================================================================
CAPA 1: FileCleanupMixin      | No tiene save(), salta a la siguiente capa.
------------------------------|-------------------------------------------------
CAPA 2: SlugFieldMixin        | 1. EJECUTA: Lógica de slugify (prepara datos).
                              | 2. LLAMA: super().save() ──┐
------------------------------|----------------------------│--------------------
CAPA 3: ProtectDefaultMixin   | 3. RECIBE el flujo <───────┘
                              | 4. EJECUTA: Validación is_default (seguridad).
                              | 5. LLAMA: super().save() ──┐
------------------------------|----------------------------│--------------------
CAPA 4: models.Model (Base)   | 6. RECIBE el flujo <───────┘
(EL FINAL DEL CAMINO)         | 7. EJECUTA: SQL UPDATE/INSERT (Persistencia).
                              | 8. RETORNA: La instancia guardada.
================================================================================
                              |
EL RETORNO (La "Bajada")      | Las funciones terminan y devuelven el control:
                              |
CAPA 3: ProtectDefaultMixin   | 9.  Retorna el resultado de super().save()
CAPA 2: SlugFieldMixin        | 10. Retorna el resultado final al usuario.
================================================================================
"""
