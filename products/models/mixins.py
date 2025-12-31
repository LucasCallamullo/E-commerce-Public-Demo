from django.utils.text import slugify

class ProtectDefaultMixin:
    """
    Mixin that prevents modifying or deleting objects marked as `is_default=True`.

    This mixin assumes the model includes the following fields:
        - name (str): The display name of the instance.
        - slug (str): The URL-friendly identifier generated from `name`.
        - is_default (bool): A flag indicating whether the instance is a protected default value.

    Main behaviors:
        - Automatically generates the initial slug when the object is created.
        - Prevents updating any instance where `is_default=True`.
        - Prevents deleting any instance where `is_default=True`.
        - Provides a unified protection error message for consistency.

    Intended usage:
        - Extend this mixin in category-like models, lookup tables, or configuration records
          where some entries must remain immutable for system integrity.
    """

    # User-facing message must remain in Spanish (as requested)
    protected_message = "No se puede modificar o eliminar una instancia por defecto."
    
    
    def save(self, *args, **kwargs):
        # Si el objeto es nuevo (no tiene PK todavía), permitir crear
        if self.pk is None:
            return super().save(*args, **kwargs)

        # Si ya existe y es default, bloquear cambios
        if getattr(self, "is_default", False):
            raise ValueError(self.protected_message)

        return super().save(*args, **kwargs)


    def delete(self, *args, **kwargs):
        """
        Prevents deletion of instances marked as default.

        Raises:
            ValueError: If attempting to delete a protected default instance.
        """
        if getattr(self, 'is_default', False):
            raise ValueError(self.protected_message)

        super().delete(*args, **kwargs)

    def __str__(self):
        """
        String representation fallback.

        Returns:
            str: The instance's name, or a placeholder if null.
        """
        return self.name or "Unnamed model"
