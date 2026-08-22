from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP
from django.db import IntegrityError

# app Core
from core.utils.utils_parsers import (
    valid_id_or_None, parse_int, parse_decimal,
    parse_bool, sanitize_text
)

# app product 
from home.services.store import StoreService
from products.models.product import Product
from products.models.brand import Brand
from products.models.category import Category
from products.models.subcategory import Subcategory

from products.services.product import ProductService


class ProductSerializer(serializers.ModelSerializer):
    
    # sobre-escribir el campo recibidio como charfield te da libertad de validarlo vos
    price_ars = serializers.CharField(required=False, allow_blank=True)
    price_usd = serializers.CharField(required=False, allow_blank=True)
    
    cost_unit = serializers.CharField(required=False, allow_null=True, write_only=True)
    stock_increment = serializers.CharField(required=False, allow_null=True, write_only=True)
    
    main_image = serializers.CharField(required=False, allow_null=True)
    # fks como charfield ya que solo se espera buscar la instancia a partir del ID
    category = serializers.CharField(required=False, allow_null=True)    
    subcategory = serializers.CharField(required=False, allow_null=True)
    brand = serializers.CharField(required=False, allow_null=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'updated_at', 'name', 'stock', 'available', 'description', 
            'main_image', 'price_ars', 'discount_ars', 'cost_avg_ars',
            'price_usd', 'discount_usd', 'is_linked_prices', 'sku',
            
            'stock_increment', 'cost_unit', 
            'category', 'subcategory', 'brand',
        ]
        extra_kwargs = {
            'id': {'read_only': True},
            'updated_at': {'read_only': True},
            'cost_avg_ars': {'read_only': True},
            'stock': {'read_only': True},
            'name': {'validators': [], 'required': False},
            'sku': {'required': False},
            'available': {'required': False},
            'description': {'required': False},
            'discount_ars': {'required': False},
            'discount_usd': {'required': False},
            'is_linked_prices': {'required': False},
        }
        
    def validate_brand(self, value) -> Brand:
        # Parse input (treats invalid strings or negatives as None)
        brand_id = valid_id_or_None(value, allow_zero=True)
        if brand_id is None:
            raise serializers.ValidationError(f"Marca: {brand_id} no es Número Entero válido.")
        
        if brand_id == 0:
            # si vino 0 o None significa que es la por defecto
            return Brand.objects.filter(is_default=True).first()
        
        # Optimization: Avoid DB query if ID hasn't changed
        if self.instance and self.instance.brand_id == brand_id:
            return self.instance.brand
        
        brand = Brand.objects.filter(id=brand_id, is_default=False).first()
        if not brand:
            # Strict approach: If an ID was provided but not found, it's an error.
            raise serializers.ValidationError(f"Marca con ID {brand_id} no existe.")
        
        return brand
        
    def validate_category(self, value) -> Category:
        # Parse input (treats invalid strings or negatives as None)
        category_id = valid_id_or_None(value, allow_zero=True)
        if category_id is None:
            raise serializers.ValidationError(f"Categoría: {category_id} no es Número Entero válido.")
        
        if category_id == 0:
            # si vino 0 o None significa que es la por defecto
            return Category.objects.filter(is_default=True).first()
        
        # Optimization: Avoid DB query if ID hasn't changed
        if self.instance and self.instance.category_id == category_id:
            return self.instance.brand
        
        category = Category.objects.filter(id=category_id, is_default=False).first()
        if not category:
            # Strict approach: If an ID was provided but not found, it's an error.
            raise serializers.ValidationError(f"Categoría con ID {category_id} no existe.")
        
        return category


    def validate_subcategory(self, value):
        """
        Validates subcategory integrity and its relationship with the parent category.
        
        Logic:
        1. Handles '0' as an explicit instruction to set subcategory to NULL.
        2. Ensures both Category and Subcategory IDs are present and valid integers.
        3. Optimization: Returns current instance if IDs haven't changed.
        4. Integrity: Verifies the Subcategory belongs to the provided Category.
        """
        subcat_id = valid_id_or_None(value, allow_zero=True)
        category_id = valid_id_or_None(self.initial_data.get("category"))
        
        # Handle explicit nullification (UI 'Sin Subcategoría' option)
        if subcat_id == 0:
            return None
        
        # Basic validation: IDs must be valid integers
        if category_id is None or subcat_id is None:
            msg = f"Categoría {category_id}" if category_id is None else f"Subcategoría {subcat_id}"
            raise serializers.ValidationError(f"{msg} no es Número Entero válido.")
            
        # Update Optimization: Return existing instance if no change detected
        if self.instance and (self.instance.subcategory_id == subcat_id and 
            self.instance.category_id == category_id):
                return self.instance.subcategory

        # Integrity Check: Filter by both IDs
        sub = Subcategory.objects.filter(id=subcat_id, category_id=category_id).first()
        if not sub:
            raise serializers.ValidationError(
                "Inconsistencia: La Subcategoría no pertenece a la Categoría seleccionada.")
        
        return sub
        
    def validate_stock_increment(self, value):
        """ Valida que el stock sea un número entero mayor o igual a 0. """
        return parse_int(value=value, field_name="Stock a Incrementar", allow_zero=True)
    
    def validate_discount_ars(self, value):
        return parse_int(value, "Descuento ARS", allow_zero=True)
    
    def validate_discount_usd(self, value):
        return parse_int(value, "Descuento USD", allow_zero=True)

    def validate_price_ars(self, value):
        """ Valida que el precio sea un número flotante mayor que 0. """
        return parse_decimal(value, "Precio ARS", allow_zero=False)
    
    def validate_price_usd(self, value):
        """ Valida que el precio sea un número flotante mayor que 0. """
        return parse_decimal(value, "Precio USD", allow_zero=True)
    
    def validate_cost_unit(self, value):
        return parse_decimal(value, "Costo Unidad", allow_zero=False)
    
    def validate_available(self, value):
        return parse_bool(value, field_name='Disponible')
    
    def validate_is_linked_prices(self, value):
        return parse_bool(value, field_name='Precio ARS Relacionado con Precio USD.')
    
    def validate_main_image(self, value):
        """ Retorna el ID de una posible imagen de ProductImage, o None """
        return valid_id_or_None(value)
    
    def validate_description(self, value):
        """ Sanitiza el contenido HTML recibido en el campo 'description'. """
        return sanitize_text(value)

    def validate_name(self, value):
        """ Valida el campo 'name': - Debe tener al menos 3 caracteres. """
        name = value.strip()
        if len(name) < 3:
            raise serializers.ValidationError(f"El Nombre: {name} debe tener una extension minima de 3 letras.")
        return name   
    
    def _validate_consistency_fields(self, attrs: dict) -> dict:
        
        # 1. Validación de Costo vs Stock (Tu lógica original)
        cost = attrs.get('cost_unit')
        stock = attrs.get('stock_increment')
        if not cost and stock:
            raise serializers.ValidationError(
                {"cost_unit": "Agregar Stock requiere ingresar el Costo por Unidad."})
            
        if cost and not stock:
            raise serializers.ValidationError(
                {"stock_increment": "Agregar Costo por Unidad requiere ingresar el nuevo Stock."})
        
        # 2. Lógica de Precios Vinculados
        # Obtenemos los valores actuales o los nuevos del request
        is_linked = attrs.get('is_linked_prices', 
            self.instance.is_linked_prices if self.instance else False)
        
        price_ars = attrs.get('price_ars')
        price_usd = attrs.get('price_usd') 
        
        if is_linked and (price_ars or price_usd):
            
            # llamo al servicio para obtener dato de la tasa de cambio
            usd_rate = StoreService.get_usd_rate()
            if not usd_rate:
                raise serializers.ValidationError(
                    {"is_linked_prices": "Todavía no hay Tasa de cambio de USD configurada en tu tienda."})
                
            usd_value = Decimal(usd_rate)
            
            # Si están linkeados, priorizamos ARS para calcular USD (o viceversa según tu regla de negocio)
            if price_ars:
                # Recalculamos USD basándonos en el nuevo precio ARS
                new_price_ars = Decimal(str(price_ars))
                calculated_usd = new_price_ars / usd_value
                # Redondeamos a 2 decimales
                attrs['price_usd'] = calculated_usd.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
            elif price_usd:
                # Si el usuario solo mandó USD, actualizamos ARS
                new_price_usd = Decimal(str(price_usd))
                calculated_ars = new_price_usd * usd_value
                attrs['price_ars'] = calculated_ars.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
        return attrs
  
    
    def validate(self, attrs):
        """
        Performs cross-field validation and enforces business rules:
        1. Skips creation-specific checks if performing a partial update (PATCH).
        2. Restricts product creation to non-seller roles (RBAC - Role-Based Access Control).
        3. Ensures the 'name' field is present during the POST process.
        """
        user = self.context.get('user')
        
        if self.instance:
            # We restrict fields that the seller cannot modify.
            protected_fields = {
                'price_ars', 'price_list', 'discount_ars',
                'price_usd', 'discount_usd', 'is_linked_prices'
            }
            # Verificamos si intentan enviar campos protegidos sin ser admin
            if user.role != 'admin':
                sent_protected_fields = protected_fields.intersection(attrs.keys())
                if sent_protected_fields:
                    raise serializers.ValidationError({
                        field: "No tienes permisos para modificar este campo." 
                        for field in sent_protected_fields
                    })
        
            return self._validate_consistency_fields(attrs)

        # Block for sellers in POST
        if user.role == 'seller':
            raise serializers.ValidationError(
                {"user": "Los Vendedores no pueden crear Productos nuevos."})
        
        # Name validation required for POST
        fields = ('name', 'price_ars', 'cost_unit', 'stock_increment')
        for field in fields:
            v = attrs.get(field, None)
            if v is None:
                raise serializers.ValidationError(
                    {field: f"El {v} es obligatorio al crear un nuevo Producto."})
        
        return self._validate_consistency_fields(attrs)
    
    def update(self, instance, validated_data):
        # prepare data for update and calls audit services
        data = {
            'old_price_ars': float(instance.price_ars),
            'old_discount_ars': float(instance.discount_ars),
            'old_price_usd': float(instance.price_usd),
            'old_discount_usd': float(instance.discount_usd),
            'old_stock': int(instance.stock),
            'user': self.context.get('user', None),
            'ip': self.context.get('ip', None),
        }
        return ProductService.handle_update(
            instance=instance, payload=validated_data, audit_data=data
        )
    
    def create(self, validated_data):
        data = {
            'user': self.context.get('user', None),
            'ip': self.context.get('ip', None),
        }
        return ProductService.handle_create(payload=validated_data, audit_data=data)

    def save(self, **kwargs):
        # como no controlamos con el validator de drf que sea el unico nombre
        # lo delegamos a la db, y capturamos la respuesta
        try:
            return super().save(**kwargs)
        except IntegrityError:
            raise serializers.ValidationError(
                {"name": "Ya existe un Producto con este nombre, Por favor, elija otro."}
            )

    def to_representation(self, instance: Product):
        # 1. Call the original method to get the default serialized data as a dictionary.
        representation = super().to_representation(instance)
        
        # this set de new main_image URL or None
        representation['main_image'] = instance.main_image if instance.main_image else None
        
        # 2. Replace specific fields with human-readable names.
        # For example, instead of returning an ID for 'category', return its name.
        expandable_fields = ['category', 'subcategory', 'brand']
        for field in expandable_fields:
            obj = getattr(instance, field, None)
            if obj:
                representation[field] = {
                    'id': obj.id,
                    'name': obj.name
                }
            else:
                representation[field] = None
        
        # 3. Return the updated dictionary as the final serialized output.
        return representation