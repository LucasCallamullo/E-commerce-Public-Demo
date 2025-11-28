

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from django.core.validators import validate_email, RegexValidator
from django.utils.html import strip_tags

from home.models import Store, StoreImage

class StoreSerializer(serializers.ModelSerializer):
    phone_regex = RegexValidator(
        regex=r'^\+?[\d\s]{8,15}$',
        message="Número inválido. Use formato: '+999999999'."
    )
    
    cellphone = serializers.CharField(
        validators=[phone_regex],
        required=False,
        max_length=20
    )
    wsp_number = serializers.CharField(
        validators=[phone_regex],
        required=False,
        max_length=20
    )
    
    def validate(self, data):
        # Sanitizar campos de texto
        text_fields = ['name', 'address', 'email', 'cellphone', 'wsp_number']
        for field in text_fields:
            if field in data:
                data[field] = strip_tags(data[field])  # Elimina etiquetas HTML
                
        # Validación adicional para URLs
        url_fields = ['ig_url', 'fb_url', 'tt_url', 'tw_url', 'google_url']
        for field in url_fields:
            if field in data and data[field]:
                url = data[field].strip()
                if not url.startswith(('http://', 'https://')):
                    url = f'https://{url}'
                data[field] = url
        return data
    
    class Meta:
        model = Store
        fields = [
            'name', 'address', 'email', 
            'cellphone', 'wsp_number',
            'ig_url', 'fb_url', 'tt_url',
            'tw_url', 'google_url'
        ]
        extra_kwargs = {
            'email': {'validators': [validate_email]},
            
            'name': {'required': False},
            'address': {'required': False},
            'wsp_number': {'required': False},
            'cellphone': {'required': False},
            
            'ig_url': {'required': False},
            'fb_url': {'required': False},
            'tt_url': {'required': False},
            'tw_url': {'required': False},
            'google_url': {'required': False},
        }


from products import utils
class StoreImageSerializer(serializers.ModelSerializer):
    """ 
        data_example = {
            "image_url": https: //...,
            "available": true,
            "main_image": false
        }
    """
    image_url = serializers.CharField(required=False, allow_null=True)
    
    def validate_main_image(self, value):
        is_new_main = utils.get_valid_bool(value, field='Main Imagen.')
        images = self.context.get("images", [])
        
        flag = False if not self.instance else self.instance.available
        is_actived = utils.get_valid_bool(self.initial_data.get("available", flag), field='Imagen Desactivada.')
        
        if is_new_main and not is_actived:
            raise serializers.ValidationError("No se puede marcar como Imagen Principal si esta oculta.")
        
        if not is_new_main and not images.exists():
            raise serializers.ValidationError("No puede ocultar la única imagen activa..")
        
        return is_new_main

    def validate_available(self, value):
        is_actived = utils.get_valid_bool(value, field='Imagen Desactivada.')    # True
        images = self.context.get("images", [])
        
        flag = False if not self.instance else self.instance.main_image
        is_new_main = utils.get_valid_bool(self.initial_data.get("main_image", flag), field='Main Imagen.')
        
        if not is_actived and is_new_main:
            raise serializers.ValidationError("No se puede ocultar la Imagen Principal.")
        
        if not is_actived and not images.exists():
            raise serializers.ValidationError("No puede ocultar la única imagen activa.")
        
        return is_actived

    def validate_image_url(self, value):
        if not value or len(value) <= 8:
            return self.instance.image_url if self.instance else None
        return value

    def update(self, instance, validated_data):
        is_new_main = validated_data.get('main_image', self.instance.main_image)
        is_actived = validated_data.get('available', self.instance.available)
        # Get other active headers for this store, excluding the current one
        images = self.context.get("images", [])
        
        # If the current one is becoming the new main image
        if is_new_main and not instance.main_image:
            to_update = []
            for h in images:
                if h.main_image:
                    h.main_image = False
                    to_update.append(h)
            if to_update:
                StoreImage.objects.bulk_update(to_update, ['main_image'])
        
        # If the current main image is being soft-deleted
        if (not is_actived or not is_new_main) and instance.main_image:
            for h in images:
                h.main_image = True
                h.save(update_fields=['main_image'])
                break
            else:
                validated_data['main_image'] = True
                validated_data['available'] = True
                return super().update(instance, validated_data)

        return super().update(instance, validated_data)
    
    def create(self, validated_data):
        is_new_main = validated_data.get('main_image')
        is_actived = validated_data.get('available')
        # Get other active headers for this store, excluding the current one
        store = self.context['store']
        image_type = self.context['image_type']
        images = self.context.get("images", [])
        has_main = any(h.main_image for h in images)

        if is_new_main and has_main:
            # Desactivar los demás main_image
            to_update = []
            for h in images:
                if h.main_image:
                    h.main_image = False
                    to_update.append(h)
            if to_update:
                StoreImage.objects.bulk_update(to_update, ['main_image'])
            
        if not is_actived and not has_main:
            # Asegura siempre una imagen principal
            validated_data['main_image'] = True
            validated_data['available'] = True
            
        validated_data['store_id'] = store.id
        validated_data['image_type'] = image_type
        
        return StoreImage.objects.create(**validated_data)

    class Meta:
        model = StoreImage
        fields = ['image_url', 'main_image', 'available']

        extra_kwargs = {
            'image_url': {'required': False},
            'main_image': {'required': False},
            'available': {'required': False},
        }