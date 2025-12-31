from rest_framework import serializers
from django.utils.text import slugify
# from django.contrib.postgres.search import SearchVector

# app audit
from audit.services.audit_service import AuditService

# product app
from products.models.product import Product
from products.models.subcategory import Subcategory
from products.models.brand import Brand

from core.utils import utils_basic

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
    
    category = serializers.SerializerMethodField()    # solo se usa como campo de validacion
    subcategory = serializers.CharField(required=False, allow_null=True)
    brand = serializers.CharField(required=False, allow_null=True)
    
    def to_representation(self, instance):
        # 1. Call the original method to get the default serialized data as a dictionary.
        representation = super().to_representation(instance)
        
        # 2. Replace specific fields with human-readable names.
        # For example, instead of returning an ID for 'category', return its name.
        representation['main_image'] = instance.main_image if instance.main_image else None
        representation['category'] = instance.subcategory.category.name if instance.subcategory else None
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

    def validate_brand(self, value):
        value = utils_basic.valid_id_or_None(value)  # Convierte '0' en None
        if not value:
            return Brand.objects.get(id=1)
        
        # 2. Optimniza retornar una fk directa sin hacer consulta extra
        if self.instance and getattr(self.instance, 'brand_id', None) == value:
            return self.instance.brand # PBrand(id=value)
        
        try:
            return Brand.objects.get(id=value)
        except Brand.DoesNotExist:
            return Brand.objects.get(id=1)

    def validate_subcategory(self, value):
        """
            Valida que la subcategoría enviada pertenezca a la categoría enviada.
            Lanza ValidationError si no es consistente.
        """
        value = utils_basic.valid_id_or_None(value)
        category_id = utils_basic.valid_id_or_None(self.initial_data.get("category"))
        
        # 1. No se puede validar subcategoría si no hay categoría válida asociada
        # Si falta subcategory o category
        if None in (value, category_id):
            return Subcategory.objects.get(id=1)
            # raise serializers.ValidationError("Debe enviar tanto categoría como subcategoría válidas.")
            
        # 2. Para update, si no cambió, devolvemos la instancia actual
        if self.instance and getattr(self.instance, 'subcategory_id', None) == value:
            return self.instance.subcategory
            
        # 3. Para en caso que eligiera una nueva validar que sea correcta su categoria filtramos
        try:
            return Subcategory.objects.get(id=value, category_id=category_id)
        except Subcategory.DoesNotExist:
            raise serializers.ValidationError("La subcategoría no pertenece a la categoría indicada.")
            # return Subcategory.objects.get(id=1)
        
    def validate_stock(self, value):
        """
        Valida que el stock sea un número entero mayor o igual a 0.
        """
        return utils_basic.parse_number(value, "Stock", allow_zero=True)
    
    def validate_discount(self, value):
        """
        Valida que el descuento sea un número entero mayor o igual a 0.
        """
        return utils_basic.parse_number(value, "Descuento", allow_zero=True)

    def validate_price(self, value):
        """
        Valida que el precio sea un número flotante mayor que 0.
        """
        return utils_basic.parse_number(value, "Precio", allow_zero=False)
    
    def validate_main_image(self, value):
        """
        Valida que la nueva url exista y sea del producto y asocia la nueva imagen, tambien viene como STR (ver Category).
        """
        value = utils_basic.valid_id_or_None(value)
        if not value:
            return None
        
        # 1. accedemos al queryset que ya viene de antes del producto
        if self.instance:
            images = self.context.get("images", [])
            
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
        return utils_basic.get_valid_bool(value, field='available')
        
    def validate_name(self, value):
        """
        Valida el campo 'name':
        - Debe tener al menos 3 caracteres.
        - En POST, es obligatorio.
        - En PUT, si no cambia, devuelve None para no actualizarlo.
        """
        if len(value) <= 2:
            raise serializers.ValidationError("El campo 'name' debe tener una extension minima de 3 letras.")
        
        # POST: self.instance es None
        if not self.instance and not value:
            raise serializers.ValidationError("El campo 'name' es obligatorio.")
        
        # PUT: si no cambia, retornamos None para evitar recalcular slug y normalized_name
        if self.instance and self.instance.name == value:
            return None
        
        return value    #  new name its time to update
    
    def validate_description(self, value):
        """
        Sanitiza el contenido HTML recibido en el campo 'description'.
        """
        return utils_basic.sanitize_text(value)
            
    def update(self, instance, validated_data):
        """ """
        # DEBUG
        print("Contenido de validated_data:")
        for key, value in validated_data.items():
            print(f"{key}: {value}")
        
        # 1 - solo dejar modificar ciertos campos a un vendedor , se pasa desde la views el context
        # 1. CAPTURAR DATOS "VIEJOS" ANTES DEL CAMBIO
        old_price = float(instance.price)
        old_stock = instance.stock
        
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
            validated_data["normalized_name"] = utils_basic.normalize_or_None(new_name)
            validated_data["slug"] = slugify(new_name)
            # este dato se calcula a partir de un trigger en la misma db asique no hace falta cambiarlo
            # manualmente, aunque igual periodicamente hacer un update no estaria mal
            # validated_data["search_vector"] = SearchVector('normalized_name', weight='A')
            
            
        # 1b. en caso de recuperar un None ( es decir sin cambios ) eliminamos del update
        else:
            validated_data.pop("name", None)

        # Guardamos los cambios
        updated_instance = super().update(instance, validated_data)
        
        # 4. AUDITORÍA: COMPARAR Y GUARDAR SI CAMBIARON
        # Solo disparamos el log si el campo venía en el request y es distinto al anterior
        
        # Auditoría de Precio
        if 'price' in validated_data:
            # en este punto ya el validated data no me hace falta porque ya lo use antes
            # new_price = float(validated_data['price'])
            new_price = float(validated_data.pop('price'))
            if new_price != old_price:
                print("old_price: ", {"price": old_price})
                print("new_price: ", {"price": new_price})
                AuditService.log_generic_product_update(
                    user=user,
                    product=updated_instance,
                    old_data={"price": old_price},
                    new_data={"price": new_price},
                    ip=self.context.get('ip') # Puedes pasarlo en el context desde la view
                )

        # Auditoría de Stock
        if 'stock' in validated_data:
            new_stock = validated_data.pop('stock')
            if new_stock != old_stock:
                AuditService.log_generic_product_update(
                    user=user,
                    product=updated_instance,
                    old_data={"stock": old_stock},
                    new_data={"stock": new_stock},
                    ip=self.context.get('ip')
                )
                
        # 4. OTROS CAMBIOS (Lo que quedó en el dict)
        # Eliminamos campos técnicos que no queremos en el log de "Otros cambios"
        validated_data.pop('slug', None)
        validated_data.pop('normalized_name', None)
            
        # en este punto ya no estan las keys stock y price, entonces si hay otros cambios logeo eso    
        if validated_data.keys():
            AuditService.log_generic_product_update(
                user=user,
                product=updated_instance,
                new_data={"product": validated_data},
                ip=self.context.get('ip')
            )
        
        return updated_instance
    
    
    def create(self, validated_data):
        # 1. Procesar campos especiales antes de crear el objeto
        name = validated_data.get("name")
        
        # Normalización y slug solo si viene un nuevo name
        if name:
            validated_data["normalized_name"] = utils_basic.normalize_or_None(name)
            validated_data["slug"] = slugify(name)
            
            # este dato se calcula a partir de un trigger en la misma db asique no hace falta cambiarlo
            # manualmente, aunque igual periodicamente hacer un update no estaria mal
            # validated_data["search_vector"] = SearchVector('normalized_name', weight='A')

        # Crear producto con select_related para evitar consultas extra
        product = Product.objects.select_related(
            "subcategory__category", "subcategory", "brand"
        ).create(**validated_data)

        return product
    
    
    def _to_audit(self):
        pass
