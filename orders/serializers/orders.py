

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.utils.utils_parsers import parse_bool, parse_decimal, sanitize_text, parse_int
from core.utils.django_helpers import get_field_attribute
from core.utils.utils_db import model_optimized_update

from core.utils.utils_parsers import valid_id_or_None
from django.utils.html import strip_tags


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