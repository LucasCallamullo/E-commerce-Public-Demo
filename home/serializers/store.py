from rest_framework import serializers

# core app
from core.utils.utils_db import model_optimized_update
from core.utils.utils_parsers import (
    sanitize_text, validate_email_format, parse_wsp_number, parse_decimal
)
# home app
from home.models import Store


class StoreSerializer(serializers.ModelSerializer):
    # Sobrescribimos para aplicar nuestra lógica personalizada de validación
    email = serializers.CharField(required=False, allow_null=True)
    
    def validate_usd_exchange_rate(self, value):
        return parse_decimal(value=value, field_name='Precio USD a ARS', allow_zero=True)
    
    def validate_wsp_number(self, value):
        return parse_wsp_number(value)
    
    def validate_email(self, value):
        return validate_email_format(value=value)
    
    def validate(self, data):
        """
        Final cross-field validation and sanitization.
        """
        text_fields = [
            'name', 'description', 'schedules', 'address', 
            'cellphone', 'wsp_number', 'bank_name', 
            'account_holder', 'cuit', 'cbu_cvu', 'alias', 'account_number'
        ]
        
        for field in text_fields:
            if field in data and data[field]:
                # Aplicamos limpieza de HTML/Scripting
                data[field] = sanitize_text(data[field])

        return data
    
    class Meta:
        model = Store
        fields = [
            'id', 'name', 'description', 'schedules', 'usd_exchange_rate',
            'address', 'email', 'cellphone', 'wsp_number',
            'bank_name', 'account_holder', 'cuit', 'cbu_cvu', 'alias', 'account_number'
        ]
        extra_kwargs = {
            'id': {'read_only': True},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """  
        Iteramos sobre los campos generados, es para setear algo como esto :
        extra_kwargs = {
            'name': {'required': False},
            'address': {'required': False},
            ...
        } 
        """
        # Dinámicamente seteamos required=False en todo lo que no sea read_only
        for field_name, field in self.fields.items():
            if not field.read_only:
                field.required = False
    
    def update(self, instance, validated_data):
        # 1. Ejecutamos la actualización
        return model_optimized_update(instance=instance, validated_data=validated_data)
    