from typing import Any
from rest_framework import serializers

# core app
from core.utils.utils_db import model_optimized_update
from core.utils.utils_parsers import (parse_url, parse_bool)
# home app
from home.models.social_media import SocialMedia


class SocialMediaSerializer(serializers.ModelSerializer):
    """
    Serializer for managing SocialMedia instances with enhanced validation.
    
    This serializer handles business logic for social media management, 
    including URL formatting, activation status consistency, and limiting 
    the maximum number of primary (main) social networks per store.
    """
    # Overriding to bypass automatic URLField validation for custom messaging
    url = serializers.CharField(required=False, allow_null=True)
    
    class Meta:
        model = SocialMedia
        fields = ['id', 'platform', 'url', 'is_main', 'is_active']
        extra_kwargs = {
            'id': {'read_only': True},
            'platform': {'read_only': True},
            'is_main': {'required': False},
            'is_active': {'required': False},
        }
        
    def validate_url(self, value: str) -> str | None:
        return parse_url(value=value)

    def validate_is_main(self, value: Any) -> bool:
        return parse_bool(value, field_name='Principal')
    
    def validate_is_active(self, value: Any) -> bool:
        return parse_bool(value, field_name='Activo')
    
    def validate(self, attrs):
        """
        Performs cross-field validation for business rule enforcement.
        
        Rules:
        1. A social network cannot be 'main' if it is 'inactive'.
        2. A store cannot exceed 4 'main' social networks.
        """
        # 1. Recuperamos valores de forma segura (soporta PATCH parcial)
        instance_is_main = self.instance.is_main if self.instance else False
        is_new_main = attrs.get('is_main', instance_is_main)
        
        # Obtenemos is_active de attrs, o de la instancia si no viene en el request
        instance_active = self.instance.is_active if self.instance else True
        is_active = attrs.get('is_active', instance_active)

        # 2. Lógica de negocio: Consistencia de visibilidad
        if is_new_main and not is_active:
            raise serializers.ValidationError({
                'is_main': 'No se puede poner como Principal una Red Social Inactiva.'
            })
        
        # 3. Lógica de negocio: Límite de redes principales (máximo 4)
        # Solo validamos si el usuario está intentando marcar como principal una que no lo era
        if is_new_main and not instance_is_main:
            store_id = self.context.get("store").get('id')
            main_count = SocialMedia.objects.filter(store_id=store_id, is_main=True).count()
            
            if main_count >= 4:
                raise serializers.ValidationError({
                    'is_main': 'No puede tener más de 4 Redes Principales.'
                })
            
        return attrs
    
    def update(self, instance, validated_data):
        """
        Updates the SocialMedia instance using an optimized service.
        
        Instead of a standard save(), it uses DRFUpdateService to ensure only 
        dirty fields (changed data) are sent to the database.
        """
        # Método para mejorar la performance del PATCH: guarda solo los campos que cambiaron
        return model_optimized_update(
            instance=instance, 
            validated_data=validated_data
        )
