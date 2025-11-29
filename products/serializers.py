
# serializers.py
from rest_framework import serializers
from django.utils.text import slugify

from products import utils
from products.models import Product, PCategory, PSubcategory, PBrand


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer para validar y actualizar productos.
    Espera datos como:
    {
        "name": "Nombre del producto",
        "price": "30.000",
        "discount": "20",
        "stock": "1",
        "available": true,
        "description": "<p>Descripción HTML</p>",
        "category": 2,
        "subcategory": 6,
        "brand": 5,
        "main_image": 20
    }
    """
    # cuando queres aplicar logica personalizada a atributos de tu modelo, DEBES reemplazar
    # su valor aceptado por el que prefieras ( en este caso DECIMAL_FIELD y URL_FIELD aceptan STR)
    price = serializers.CharField()
    
    # utilizamos esta forma para personalizar las entradas y salidas de relaciones fk o manytomany
    main_image = serializers.CharField(required=False, allow_null=True)
    category = serializers.CharField(required=False, allow_null=True)    # Permite '0' para setear a None
    subcategory = serializers.CharField(required=False, allow_null=True)
    brand = serializers.CharField(required=False, allow_null=True)
    
    def to_representation(self, instance):
        # 1. Call the original method to get the default serialized data as a dictionary.
        representation = super().to_representation(instance)
        
        # 2. Replace specific fields with human-readable names.
        # For example, instead of returning an ID for 'category', return its name.
        representation['main_image'] = instance.main_image if instance.main_image else None
        representation['category'] = instance.category.name if instance.category else None
        representation['subcategory'] = instance.subcategory.name if instance.subcategory else None
        representation['brand'] = instance.brand.name if instance.brand else None
        
        # 3. Return the updated dictionary as the final serialized output.
        return representation
    
    class Meta:
        model = Product
        fields = [
            'name', 'price', 'stock', 'available', 'description', 'discount', 
            'main_image', 'category', 'subcategory', 'brand'
        ]

    def validate_category(self, value):
        # Tomar en cuenta que esta validación funciona y las subsecuentes relaciones de FK hacen esto
        # Pese a ser una relacion fk, en drf pedimos el valor como str y hacemos nuestra propia validacion
        
        # 1. Valuamos el STR que llega desde el front/json que se un INT positivo
        value = utils.valid_id_or_None(value)  # Convierte '0' en None
        if not value: # La lógica de esto que desde el front mandamos un 0 para quitar la Category asociada y poner la default
            return PCategory.get_default_model_or_id(model=True)
        
        # 2. Optimniza retornar una fk directa sin hacer consulta extra
        if self.instance and getattr(self.instance, 'category_id', None) == value:
            return self.instance.category # PCategory(id=value)
        
        # 3. Si en cuentra una categoría valida directamente devuelve el "Objeto" y lo asocia como FK
        try:
            return PCategory.objects.get(id=value)
        # 4. En este caso si intenta asociar una Categoria que no existe devuelve la categoría por defecto significando que se quedo sin
        except PCategory.DoesNotExist:
            return PCategory.get_default_model_or_id(model=True)

    def validate_brand(self, value):
        value = utils.valid_id_or_None(value)  # Convierte '0' en None
        if not value:
            return PBrand.get_default_model_or_id(model=True)
        # 2. Optimniza retornar una fk directa sin hacer consulta extra
        if self.instance and getattr(self.instance, 'brand_id', None) == value:
            return self.instance.brand # PBrand(id=value)
        try:
            return PBrand.objects.get(id=value)
        except PBrand.DoesNotExist:
            return PBrand.get_default_model_or_id(model=True)

    def validate_subcategory(self, value):
        # obtiene el STR de la category anterior validadandola
        value = utils.valid_id_or_None(value)  # Convierte '0' en None
        category_id = utils.valid_id_or_None(self.initial_data.get("category"))
        
        # 1. No se puede validar subcategoría si no hay categoría válida asociada
        if None in (value, category_id):
            return PSubcategory.get_default_model_or_id(model=True)
        
        # 2. Validar coherencia de category con la subcategory retornar directo si no hubo cambios
        if self.instance and getattr(self.instance, 'category_id', None) == category_id: 
            if getattr(self.instance, 'subcategory_id', None) == value:
                return self.instance.subcategory # PSubcategory(id=value)
            
        # 3. Para en caso que eligiera una nueva validar que sea correcta su categoria filtramos 
        # por su fk_field
        try:
            return PSubcategory.objects.get(id=value, category_id=category_id)
        except PSubcategory.DoesNotExist:
            return PSubcategory.get_default_model_or_id(model=True)
        
    def validate_stock(self, value):
        """
        Valida que el stock sea un número entero mayor o igual a 0.
        """
        return utils.parse_number(value, "Stock", allow_zero=True)
    
    def validate_discount(self, value):
        """
        Valida que el descuento sea un número entero mayor o igual a 0.
        """
        return utils.parse_number(value, "Descuento", allow_zero=True)

    def validate_price(self, value):
        """
        Valida que el precio sea un número flotante mayor que 0.
        """
        return utils.parse_number(value, "Precio", allow_zero=False)
    
    def validate_main_image(self, value):
        """
        Valida que la nueva url exista y sea del producto y asocia la nueva imagen, tambien viene como STR (ver Category).
        """
        value = utils.valid_id_or_None(value)
        if not value:
            return None
        
        # 1. accedemos al prefetch queryset que ya viene de antes del producto
        images = self.context.get("images", [])
        if self.instance:
            for img in images:

                # 2. encontramos la imagen a actuailizar y llamamos al metodo de ProductImage
                if img.id == value:
                    img.update_main_image(images)
                    return img.image_url

        return None    # 3. si por algun motivo (se esta creando) falla retornamos None, logica de asignar en ProductImage

    def validate_available(self, value):
        """
        Asegura que el campo 'available' sea booleano válido,
        incluso si llega como string desde el front.
        """
        return utils.get_valid_bool(value, field='available')
        
    def validate_name(self, value):
        # Solo validamos 'name' para evitar actualizar slug y normalized_name si no cambia.
        # El resto de campos se actualiza siempre (no afecta lógica interna ni rendimiento).
        if len(value) <= 2:
            raise serializers.ValidationError("El campo 'name' debe tener una extension minima de 3 letras.")
        if self.instance and self.instance.name == value:
            return None  # no cambia
        return value    #  new name its time to update
    
    def validate_description(self, value):
        """
        Sanitiza el contenido HTML recibido en el campo 'description'.
        """
        return utils.sanitize_text(value)
            
    def update(self, instance, validated_data):
        """ """
        # Imprimir todas las claves y valores de validated_data
        print("Contenido de validated_data:")
        for key, value in validated_data.items():
            print(f"{key}: {value}")
        
        # 1 - solo dejar modificar ciertos campos a un vendedor , se pasa desde la views el context
        user = self.context['user']
        if user.role == 'seller':
            # 2 - Restringimos campos que no puede modificar el vendedor
            removed = []
            for field in ['price', 'price_list', 'discount']:
                if field in validated_data:
                    validated_data.pop(field)
                    removed.append(field)
            if removed:
                print(f"Seller intentó modificar campos restringidos: {removed}")
            # 3 - Terminamos el update parcial con los campos que queden en validated_data
            return super().update(instance, validated_data)
        

        # 1. Procesar 'name' si es un nuevo value antes del update
        new_name = validated_data.get("name")
        if new_name:
            validated_data["normalized_name"] = utils.normalize_or_None(new_name)
            validated_data["slug"] = slugify(new_name)
        # 1b. en caso de recuperar un None ( es decir sin cambios ) eliminamos del update
        else:
            validated_data.pop("name", None)

        # 2. Hacer el update con todos los campos, incluido 'name', si vino
        return super().update(instance, validated_data)

    def create(self, validated_data):
        # 1. Procesar campos especiales antes de crear el objeto
        name = validated_data.get("name")
        
        # 2. stupid check
        if not name:
            raise serializers.ValidationError("El campo nombre es obligatorio.")

        validated_data["normalized_name"] = utils.normalize_or_None(name)
        validated_data["slug"] = slugify(name)
            
        # 3. Traer el producto con select_related para evitar consultas extra al serializar
        product = Product.objects.select_related(
            "category", "subcategory", "brand"
        ).create(**validated_data)

        return product


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
            flag = utils.get_valid_bool(value, field='image_url')
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
        model = PSubcategory
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
        category_id = utils.valid_id_or_None(value)
        if not category_id:
            raise serializers.ValidationError("ID de categoría inválido.")

        # 2. Si es una actualización y la categoría no cambió, retornar la actual
        if self.instance and self.instance.category_id == category_id:
            return self.instance.category
        
        # 3. Obtener la categoría (o error si no existe)
        try:
            category = PCategory.objects.prefetch_related('subcategories').get(id=category_id)
        except PCategory.DoesNotExist:
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
        model = PCategory
        fields = ['name', 'image_url']
        extra_kwargs = {
            'name': {'required': False},
            'image_url': {'required': False},
        }


class PBrandSerializer(BaseModelSerializer):
    class Meta:
        model = PBrand
        fields = ['name', 'image_url']
        extra_kwargs = {
            'name': {'required': False},
            'image_url': {'required': False},
        }
        
        











class CleanNullFieldsSerializer(serializers.Serializer):
    """
    Base serializer that optionally removes fields with None, '', or [] values.
    Controlled by 'clean_nulls' in context (default: True).
    """
    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Check if cleaning is enabled in the context (default True)
        if not self.context.get('clean_nulls', True):
            return data

        return {k: v for k, v in data.items() if v not in (None, '', [])}


class BrandListSerializer(CleanNullFieldsSerializer):
    id = serializers.IntegerField()
    slug = serializers.CharField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_null=True)
    image_url = serializers.URLField(required=False, allow_null=True)
    is_default = serializers.BooleanField(required=False)

class CategoryListSerializer(CleanNullFieldsSerializer):
    id = serializers.IntegerField()
    slug = serializers.CharField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_null=True)
    image_url = serializers.URLField(required=False, allow_null=True)
    is_default = serializers.BooleanField(required=False)

class SubcategoryListSerializer(CleanNullFieldsSerializer):
    id = serializers.IntegerField()
    slug = serializers.CharField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_null=True)
    image_url = serializers.URLField(required=False, allow_null=True)
    is_default = serializers.BooleanField(required=False)


class ProductListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    slug = serializers.CharField(required=False, allow_null=True)
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_list = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    available = serializers.BooleanField(required=False, allow_null=True)
    stock = serializers.IntegerField()
    discount = serializers.IntegerField()
    updated_at = serializers.DateTimeField(required=False, allow_null=True)
    main_image = serializers.CharField(required=False, allow_null=True)
    
    # its a bool to identify liked products
    is_favorited = serializers.SerializerMethodField()
    
    # only send ID to prevent big response data
    brand_id = serializers.IntegerField()
    category_id = serializers.IntegerField()
    subcategory_id = serializers.IntegerField()
    
    
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # conservar price_list aunque sea null
        allowed_nulls = {'price_list'}
        return {k: v for k, v in rep.items() if v is not None or k in allowed_nulls}


    def get_is_favorited(self, obj):
        favorites_ids = self.context.get('favorites_ids', None)
        if not favorites_ids:
            return False
        return obj['id'] in favorites_ids
    
    
    """
    def _get_related_data(self, obj, prefix, default_fields, serializer_class, context_key=None):
        
        Extrae y serializa datos relacionados desde un diccionario de `values()`.

        Args:
            obj (dict): Diccionario con los datos de la instancia y sus relaciones,
                        por ejemplo proveniente de queryset.values().
            prefix (str): Prefijo del nombre de la relación, e.g., 'brand', 'category'.
            default_fields (list[str]): Lista de campos por defecto a incluir.
            serializer_class (Serializer): Clase de serializer a usar para formatear la salida.
            context_key (str, optional): Clave opcional para buscar campos en `self.context`.

        Returns:
            dict | None: Diccionario serializado con los datos de la relación, o None si
                        no aplica (por ejemplo, si la relación está vacía o es "default").
        

        # 1- Verificar que exista el id de la relación y que no sea "default"
        # or obj.get(f'{prefix}__is_default')
        if not obj.get(f'{prefix}__id'):
            return None

        # 2- Determinar los campos a incluir: usar contexto o defaults
        keys = self.context.get(context_key or f'{prefix}_fields', default_fields)

        # 3- Extraer valores de obj con el prefijo indicado, solo si no son None
        data = {
            key: obj.get(f'{prefix}__{key}')
            for key in keys
            if obj.get(f'{prefix}__{key}') is not None
        }
        # 4- Serializar y devolver
        serializer = serializer_class(data)
        return serializer.data

    def get_brand(self, obj):
        return self._get_related_data(
            obj=obj,
            prefix='brand',
            default_fields=['id', 'slug', 'name'],
            serializer_class=BrandListSerializer,
            context_key='brand_fields'
        )

    def get_category(self, obj):
        return self._get_related_data(
            obj=obj,
            prefix='category',
            default_fields=['id', 'slug', 'name'],
            serializer_class=CategoryListSerializer,
            context_key='category_fields'
        )

    def get_subcategory(self, obj):
        return self._get_related_data(
            obj=obj,
            prefix='subcategory',
            default_fields=['id', 'slug', 'name'],
            serializer_class=SubcategoryListSerializer,
            context_key='subcategory_fields'
        )
    """