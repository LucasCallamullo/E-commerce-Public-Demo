from django.db import IntegrityError, transaction
from rest_framework import serializers

# core app
from core.utils.utils_parsers import parse_bool, valid_id_or_None
from core.utils.utils_db import model_optimized_update

# products app
from products.models.category import Category
from products.models.subcategory import Subcategory
from products.models.brand import Brand

import logging
logger = logging.getLogger(__name__)
    
# for category, subcategory and brand
class BaseModelSerializer(serializers.ModelSerializer):
    
    # La forma de recibir una lista iterable desde el front
    delete_images = serializers.BooleanField(write_only=True, required=False, default=False)
    
    # se utiliza esta forma para personalizar la entrada de una url.
    image_url = serializers.CharField(required=False, allow_null=True)
    
    class Meta:
        # No definimos 'model' ni 'fields' aquí (se hará en cada hijo)
        abstract = True  # Esto evita que Django lo considere como un serializer concreto
        
    def validate_delete_images(self, value) -> bool:
        if not self.instance:
            return False
        
        return parse_bool(value=value, field_name='delete_images')
        
    def validate_image_url(self, value) -> str:
        # caso actualizacion que simplemente devolvemos el valor almacenado
        if self.instance:
            url_now = self.instance.image_url
            if url_now == value:
                return value
            
        # retorna la url como str o None
        return value
        
    def validate_name(self, value) -> str:
        if len(value) <= 2:
            raise serializers.ValidationError("El nombre debe tener al menos 3 caracteres.")
        return value.strip()
    
    def validate(self, attrs):
        """
        Object-level validation.
        Ensures 'name' is present during creation.
        """
        # Si estamos CREANDO (no hay instancia) y no viene el nombre
        if not self.instance and not attrs.get('name'):
            raise serializers.ValidationError({
                "name": "El nombre es obligatorio al crear una nueva ."
            })  
        return attrs
    
    @transaction.atomic
    def update(self, instance: Brand | Subcategory | Category, validated_data):
        """
        Updates the instance and prepares data for potential file deletion.
        
        NOTE: This method only updates the 'image_url' field in the database. 
        Physical file deletion from storage is handled asynchronously via 
        pre_save/post_save signals to ensure atomicity and separation of concerns.
        """
        # is_delete is a boolean (calculated in validate_delete_images) 
        # indicating if the current instance's ID was in the deletion list.
        is_delete = validated_data.pop("delete_images", False)
        new_image = validated_data.get('image_url')

        # Case: User explicitly requested deletion and didn't provide a new replacement.
        if is_delete and not new_image:
            validated_data["image_url"] = None
        
        # el SlugFieldMixin del modelo comparará los valores name y actuará
        # y agregá a la lista de updated_fields el slug o no.
        return model_optimized_update(instance, validated_data)


    def create(self, validated_data):
        """
        Creates a new instance, ensuring slug generation and cleaning auxiliary flags.
        """
        validated_data.pop("delete_images", None)

        # el SlugFieldMixin del modelo comparará los valores name y actuará
        # y agregá a la lista de updated_fields el slug o no.
        return self.Meta.model.objects.create(**validated_data)
    
    
    def save(self, **kwargs):
        """
        Overrides the standard save method to optimize database performance by
        leveraging "Optimistic Concurrency Control".

        Instead of performing a pre-save 'SELECT' query to validate uniqueness (the 
        DRF default), this method attempts a direct 'INSERT/UPDATE' and handles 
        potential conflicts via exception catching.

        Performance Gains:
            - Reduces database round-trips from 2 to 1 for successful creations.
            - Eliminates race conditions between validation and persistence.

        Raises:
            serializers.ValidationError: If the database returns an IntegrityError 
            (e.g., duplicate 'name' or 'slug'), it is caught and re-raised as a 
            clean API error for the frontend.
        """
        try:
            return super().save(**kwargs)
        except IntegrityError:
            # Detectamos si es una subcategoría para dar un mensaje más preciso
            model_name = self.Meta.model.__name__
            
            if model_name == 'Subcategory':
                msg = "Ya existe una Subcategoría con este nombre en la Categoría seleccionada."
                
            # We assume the integrity failure is due to a duplicate unique field 
            # (name/slug) as defined in the model constraints.
            else:
                n = "Categoría" if model_name == 'Category' else 'Marca'
                msg = f"Este nombre de {n} ya está en uso. Por favor, elija otro."
                
            raise serializers.ValidationError({"name": msg})


class SubcategorySerializer(BaseModelSerializer):
    # Se plantea como str para usar mi propia validación
    category = serializers.CharField(required=False)  # Campo adicional
    
    class Meta:
        model = Subcategory
        fields = ['id', 'slug', 'name', 'image_url', 'category', 'delete_images']
        extra_kwargs = {
            'id': {'read_only': True},
            'slug': {'read_only': True},
            'name': {'required': False},
            'image_url': {'required': False},
            'delete_images': {'required': False},
        }
        # Esto quita la validación automática de unique_together
        # para que no salte en 'non_field_errors'
        validators = []

    def to_representation(self, instance):
        # 1. Call the original method to get the default serialized data as a dictionary.
        representation = super().to_representation(instance)
        
        # 2. Replace specific fields with human-readable names.
        # For example, instead of returning an ID for 'category', return its name.
        if instance.category:
            representation['category'] = {
                'id': instance.category.id,
                'name': instance.category.name
            }
        else:
            representation['category'] = None
        
        # 3. Return the updated dictionary as the final serialized output.
        return representation
        
    def validate_category(self, value):
        # 1. Validar formato del ID
        category_id = valid_id_or_None(value)
        if not category_id:
            raise serializers.ValidationError("ID de Categoría inválido.")

        # 2. Si es una actualización y la categoría no cambió, retornar la actual
        if self.instance and self.instance.category_id == category_id:
            return self.instance.category
        
        # 3. Obtener la categoría (o en caso de no exisitir se asignará como padre)
        # la categoría por default
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            category = Category.objects.filter(is_default=True).first()
        
        return category
    
    def validate(self, attrs):
        category = attrs.get('category', None)
        is_delete = attrs.get('delete_images', False)
        if not category and not is_delete:
            raise serializers.ValidationError("Por favor elija una Categoría para asignar.")
        
        return super().validate(attrs)
        
    def create(self, validated_data):
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class CategorySerializer(BaseModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'image_url', 'delete_images']
        extra_kwargs = {
            'id': {'read_only': True},
            'slug': {'read_only': True},
            'name': {'validators': [], 'required': False},
            'image_url': {'required': False},
            'delete_images': {'required': False},
        }


class BrandSerializer(BaseModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'image_url', 'delete_images']
        extra_kwargs = {
            'id': {'read_only': True},
            'slug': {'read_only': True},
            'name': {'validators': [], 'required': False},
            'image_url': {'required': False},
            'delete_images': {'required': False},
        }
