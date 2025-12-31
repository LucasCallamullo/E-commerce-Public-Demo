from rest_framework import serializers
from django.utils.text import slugify

from products.models.category import Category
from products.models.subcategory import Subcategory
from products.models.brand import Brand

from core.utils import utils_basic

# for category, subcategory and brand
class BaseModelSerializer(serializers.ModelSerializer):
    # se utiliza esta forma para personalizar la entrada de una url.
    image_url = serializers.CharField(required=False, allow_null=True)
    
    class Meta:
        # No definimos 'model' ni 'fields' aquí (se hará en cada hijo)
        abstract = True  # Esto evita que Django lo considere como un serializer concreto
    
    def validate_image_url(self, value):
        # debido a que el bool llegaba como un bool se tuvo que cambiar a str en formulario de .js
        if value.lower() in ('true', 'false'):
            # caso que pida borrar la imagen (setear en None) explicitamente marcando la casilla
            flag = utils_basic.get_valid_bool(value, field='image_url')
            if flag:
                return None
                
            # caso actualizacion que simplemente devolvemos el valor almacenado
            if self.instance:
                url_now = getattr(self.instance, 'image_url', None)
                return url_now
        
        # caso de actualizacion donde viene un value distinto del bool como str si a este punto creando
        # todavía vale 'false' se devolvera none, sino paso anterior se devuelve el valor almacenado
        return value if value != 'false' else None
        
    def validate_name(self, value):
        if len(value) <= 2:
            raise serializers.ValidationError("El nombre debe tener al menos 3 caracteres.")
        
        if self.instance and self.instance.name == value:
            return None
        
        # Verifica unicidad del nombre en el modelo actual (usando self.Meta.model)
        if self.Meta.model.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Ya existe un registro con este nombre.")
        return value
    
    def update(self, instance, validated_data):
        new_name = validated_data.get("name")
        new_category = validated_data.get("category", None)
        new_image_url = validated_data.get("image_url")
        
        if new_name:
            validated_data["slug"] = slugify(new_name)
        else:
            validated_data.pop("name", None)
            
            # Comparación para evitar actualización innecesaria
            if ((new_category is None or new_category == instance.category_id) and
                new_image_url == getattr(instance, 'image_url', None)):
                return instance
            
        return super().update(instance, validated_data)
        
    def create(self, validated_data):
        validated_data["slug"] = slugify(validated_data["name"])
        return self.Meta.model.objects.create(**validated_data)


class PSubcategorySerializer(BaseModelSerializer):
    category = serializers.CharField(required=True)  # Campo adicional
    
    class Meta:
        model = Subcategory
        fields = ['name', 'image_url', 'category']
        extra_kwargs = {
            'name': {'required': False},
            'image_url': {'required': False},
        }

    def to_representation(self, instance):
        # 1. Call the original method to get the default serialized data as a dictionary.
        representation = super().to_representation(instance)
        
        # 2. Replace specific fields with human-readable names.
        # For example, instead of returning an ID for 'category', return its name.
        representation['category'] = instance.category.name if instance.category else None
        
        # 3. Return the updated dictionary as the final serialized output.
        return representation
        
    def validate_category(self, value):
        # 1. Validar formato del ID
        category_id = utils_basic.valid_id_or_None(value)
        if not category_id:
            raise serializers.ValidationError("ID de categoría inválido.")

        # 2. Si es una actualización y la categoría no cambió, retornar la actual
        if self.instance and self.instance.category_id == category_id:
            return self.instance.category
        
        # 3. Obtener la categoría (o error si no existe)
        try:
            category = Category.objects.prefetch_related('subcategories').get(id=category_id)
        except Category.DoesNotExist:
            raise serializers.ValidationError("La categoría no existe.")

        # 4. Validar que la subcategoría pertenezca a la nueva categoría (solo para updates)
        # if self.instance:
        #    if not category.subcategories.filter(id=self.instance.id).exists():
        #        raise serializers.ValidationError("Esta subcategoría no pertenece a la categoría seleccionada.")
        if category.is_default:
            raise serializers.ValidationError("No se le puede asignar una categoría por defecto a la subcategoría.")
        
        return category  # Retorna el objeto category para asociación
        
    def create(self, validated_data):
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Actualiza category con el que venga por defecto
        return super().update(instance, validated_data)


class PCategorySerializer(BaseModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'image_url']
        extra_kwargs = {
            'name': {'required': False},
            'image_url': {'required': False},
        }


class PBrandSerializer(BaseModelSerializer):
    class Meta:
        model = Brand
        fields = ['name', 'image_url']
        extra_kwargs = {
            'name': {'required': False},
            'image_url': {'required': False},
        }
