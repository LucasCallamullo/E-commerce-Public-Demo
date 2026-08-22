from rest_framework import serializers
# core app
from core.utils.utils_parsers import parse_bool, parse_decimal, sanitize_text, parse_int
from core.utils.django_helpers import get_field_attribute
from core.utils.utils_db import model_optimized_update

from orders.models import ShipmentMethod, PaymentMethod


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'time', 'is_active', 'description']
        extra_kwargs = {
            'id': {'read_only': True},
            'name': {'read_only': True},
            'time': {'required': False},
            'is_active': {'required': False},
            'description': {'required': False},
        }
    
    def validate_time(self, value):
        """
        Validate processing time. 
        Enforces an operational limit of 48 hours for payment clearance.
        """
        value = parse_int(value=value, field_name="Tiempo", allow_zero=True) # 0 +
        if value > 48:  # 48 horas
            raise serializers.ValidationError("El tiempo máximo razonable es 48 horas (48 horas)")
        return value

    def validate_description(self, value):
        """
        Sanitize input and enforce database length constraints.
        Prevents XSS/HTML injection via sanitize_text.
        """
        value = sanitize_text(value)
        limit = get_field_attribute(self.Meta.model, 'description', 'max_length')
        
        if limit and len(value) > limit:
            detail = f"La descripción del método de pago no puede exceder {limit} caracteres"
            raise serializers.ValidationError(detail=detail)
            
        return value 
    
    def update(self, instance, validated_data):
        # Optimized update: only triggers SQL for modified fields
        return model_optimized_update(instance=instance, validated_data=validated_data)


class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentMethod
        fields = ['id', 'name', 'price', 'is_active', 'description']
        extra_kwargs = {
            'id': {'read_only': True},
            'name': {'read_only': True},
            'price': {'required': False},
            'is_active': {'required': False},
            'description': {'required': False},
        }
        
    def validate_price(self, value):
        return parse_decimal(value=value, field_name="Precio")
    
    def validate_is_active(self, value):
        return parse_bool(value=value, field_name="Activo")

    def validate_description(self, value):
        """
        Sanitize input and enforce database length constraints.
        Prevents XSS/HTML injection via sanitize_text.
        """
        value = sanitize_text(value)
        # 2. Validamos la lógica de negocio (longitud)
        limit = get_field_attribute(self.Meta.model, 'description', 'max_length')
        
        if limit and len(value) > limit:
            detail = f"La descripción del método de envío no puede exceder {limit} caracteres"
            raise serializers.ValidationError(detail=detail)
            
        return value

    def validate(self, attrs):
        """
        Business Rule: An active shipment method must have a price defined.
        """
        # Usamos los valores de attrs o los de la instancia actual como fallback
        is_active = attrs.get('is_active', self.instance.is_active if self.instance else True)
        price = attrs.get('price', self.instance.price if self.instance else None)
        
        if is_active and (price is None):
            raise serializers.ValidationError({
                "price": "Los métodos activos deben tener un precio definido."
            })
        
        return attrs

    def update(self, instance, validated_data):
        # Optimized update: only triggers SQL for modified fields
        return model_optimized_update(instance=instance, validated_data=validated_data)

