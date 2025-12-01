

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils.html import strip_tags

from orders.models import ShipmentMethod, PaymentMethod


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['name', 'time', 'is_active', 'description']
        read_only_fields = ['id']  # Lo marcamos como solo lectura
        extra_kwargs = {
            'name': {'required': False},
            'time': {'required': False},
            'is_active': {'required': False},
            'description': {'required': False},
        }
    
    def validate_name(self, value):
        """Valida y sanitiza el nombre"""
        if value:
            value = strip_tags(value).strip()
            if len(value) < 2:
                raise serializers.ValidationError("El nombre debe tener al menos 2 caracteres")
            if not value.replace(' ', '').isprintable():
                raise serializers.ValidationError("El nombre contiene caracteres no permitidos")
        return value

    def validate_time(self, value):
        """Valida el tiempo de procesamiento"""
        if value is not None:
            if not isinstance(value, int):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    raise serializers.ValidationError("El tiempo debe ser un número entero")
            
            if value < 0:
                raise serializers.ValidationError("El tiempo no puede ser negativo")
            if value > 48:  # 24 horas en minutos
                raise serializers.ValidationError("El tiempo máximo razonable es 48 horas (48 horas)")
        return value

    def validate_description(self, value):
        """Sanitiza la descripción"""
        if value:
            value = strip_tags(value).strip()
            if len(value) > 100:
                raise serializers.ValidationError("La descripción no puede exceder 100 caracteres")
        return value    
    

from decimal import Decimal, InvalidOperation
class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentMethod
        fields = ['name', 'price', 'is_active', 'description']
        read_only_fields = ['id']  # Lo marcamos como solo lectura
        extra_kwargs = {
            'name': {'required': False},
            'price': {'required': False},
            'is_active': {'required': False},    # its a bool
            'description': {'required': False},
        }

    def validate_price(self, value):
        """Maneja strings y valida el precio decimal"""
        if isinstance(value, str):
            try:
                value = Decimal(value.replace(',', '.'))  # Soporta ambos formatos decimales
            except (InvalidOperation, ValueError):
                raise serializers.ValidationError("Formato de precio inválido. Use números con punto decimal.")
        
        if value is not None:
            if value < Decimal('0.00'):
                raise serializers.ValidationError("El precio no puede ser negativo")
            if value.as_tuple().exponent < -2:  # Más de 2 decimales
                raise serializers.ValidationError("Máximo 2 decimales permitidos")
        
        return value

    def validate_name(self, value):
        """Validación para el nombre"""
        if value:
            value = value.strip()
            if len(value) < 2:
                raise serializers.ValidationError("El nombre debe tener al menos 2 caracteres")
            if any(char in value for char in '<>\\'):
                raise serializers.ValidationError("Caracteres no permitidos en el nombre")
        return value

    def validate_description(self, value):
        """Sanitiza la descripción"""
        if value:
            value = strip_tags(value).strip()
            if len(value) > 100:
                raise serializers.ValidationError("La descripción no puede exceder 100 caracteres")
        return value   

    def validate(self, data):
        """Validaciones cruzadas"""
        # Si está activo, debe tener precio definido
        if data.get('is_active', True) and 'price' in data and data['price'] is None:
            raise serializers.ValidationError(
                {"price": "Los métodos activos deben tener un precio definido"}
            )
        
        # Sanitización adicional
        if 'name' in data and data['name']:
            data['name'] = data['name'].strip()
        
        return data


from products.utils import valid_id_or_None
class OrderFormSerializer(serializers.Serializer):
    """
    This serializer is used to temporarily store order data from a form.
    
    It includes customer personal details, optional shipping or pickup 
    information, and payment method selection.
    """
    # Customer personal details
    first_name = serializers.CharField() 
    last_name = serializers.CharField()  
    email = serializers.EmailField()
    cellphone = serializers.CharField() 
    dni = serializers.CharField()
    detail_order = serializers.CharField(required=False, allow_blank=True)  
    # Optional order details (e.g., additional notes)

    # Shipping address fields (initially optional)
    province = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_blank=True) 
    detail = serializers.CharField(required=False, allow_blank=True)  
    # Additional address details (e.g., apartment number)

    # Local pickup details (initially optional)
    name_retire = serializers.CharField(required=False, allow_blank=True)  
    # Name of the person picking up the order
    dni_retire = serializers.CharField(required=False, allow_blank=True)  
    # ID number of the person picking up the order

    # Shipping and payment method selection
    shipping_method_id = serializers.CharField(required=False)  
    # ID of the selected shipping method
    payment_method_id = serializers.CharField(required=False)  
    # ID of the selected payment method

    def validate(self, data):
        shipping_fields = {
            'province': "Provincia",
            'city': "Ciudad",
            'address': "Dirección"
        }

        retire_fields = {
            'name_retire': "Nombre quien retira",
            'dni_retire': "DNI quien retira"
        }

        # Get Shipping Method
        shipping_method = valid_id_or_None(data.get("shipping_method_id"))
        payment_method = valid_id_or_None(data.get("payment_method_id"))
        
        if not shipping_method or not payment_method:
            raise ValidationError("Algo sucedió mal, recargue la página.")
        
        # validación para quitar etiquetas html directamente
        fields = [
            'detail_order', 'detail', 'address', 'province', 
            'city', 'name_retire', 'first_name', 'last_name'
        ]
        for field in fields:
            if field in data and isinstance(data[field], str):
                data[field] = strip_tags(data.get(field, '')).strip()
        
        if shipping_method in ["1", 1]:  # If is local retire
            for field, translated_name in retire_fields.items():
                if not data.get(field, "").strip():
                    raise ValidationError({translated_name: "Este campo no puede estar vacío."})

        else:  # Si es envío a domicilio
            for field, translated_name in shipping_fields.items():
                if not data.get(field, "").strip():
                    raise ValidationError({translated_name: "Este campo no puede estar vacío."})

        return data


