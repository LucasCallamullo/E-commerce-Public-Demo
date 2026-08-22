
from django.contrib.auth import get_user_model
from rest_framework import serializers

from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

CustomUser = get_user_model()

class RegisterLoginSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    
    # Campos opcionales SIN min_length en la definición
    dni = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=20,  # Solo max_length, NO min_length
    )
    
    cellphone = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=20,  # Solo max_length, NO min_length
    )

    class Meta:
        model = CustomUser
        fields = ("email", "password", "first_name", "last_name", 
                 "cellphone", "province", "address", "dni")
        
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": False, "allow_blank": True},
            "last_name": {"required": False, "allow_blank": True},
            "province": {"required": False, "allow_blank": True},
            "address": {"required": False, "allow_blank": True},
        }
        
    def validate_email(self, value):
        """Ensures the email has a valid format and is not already in use."""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo ya está registrado.")
        return value

    def validate_password(self, value):
        """Applies Django's password validation rules for security."""
        try:
            validate_password(value)
        except ValidationError as e:
            translated_errors = []
            for msg in e.messages:
                if "too short" in msg:
                    translated_errors.append("La contraseña es demasiado corta.")
                elif "too common" in msg:
                    translated_errors.append("La contraseña es demasiado común.")
                else:
                    translated_errors.append("La contraseña no es válida.")
            raise serializers.ValidationError(translated_errors)
        return value
    
    def validate_dni(self, value):
        """Valida DNI solo si tiene contenido"""
        # Si es None, "", o solo espacios → válido (es opcional)
        if not value or not value.strip():
            return ""  # Normaliza a string vacío
        
        # Ahora sí valida longitud
        if not (6 <= len(value) <= 20):
            raise serializers.ValidationError(
                "El DNI debe tener entre 6 y 20 caracteres."
            )
        return value
    
    def validate_cellphone(self, value):
        """Valida celular solo si tiene contenido"""
        if not value or not value.strip():
            return ""  # Normaliza a string vacío
        
        if not (6 <= len(value) <= 20):
            raise serializers.ValidationError(
                "El celular debe tener entre 6 y 20 caracteres."
            )
        return value
    
    def validate(self, data):
        """Validación final del objeto"""
        # Normaliza campos vacíos
        for field in ['dni', 'cellphone', 'first_name', 'last_name', 
                     'province', 'address']:
            if field in data and (data[field] is None or data[field].strip() == ""):
                data[field] = ""
        
        return data
    
    def create(self, validated_data):
        """Crea usuario, campos vacíos se guardan como strings vacíos"""
        return CustomUser.objects.create_user(**validated_data)


class WidgetLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Validates user-provided credentials in order to authenticate a user
        and provide meaningful validation feedback.

        Args:
            data (dict):
                Dictionary containing the JSON payload received from the login form.
                Expected keys: 'email' and 'password'.

        Raises:
            ValidationError:
                - If the email is not registered in the system.
                - If the email exists but the provided password is incorrect.

        Returns:
            dict:
                A dictionary containing:
                - 'user' (CustomUser): The authenticated user instance, which can
                  later be used to log the user into the Django session.
        """
        email = data.get("email")
        password = data.get("password")
        
        # Query 1: Fetch the full user object (not just an existence check)
        try:
            user = CustomUser.objects.get(email=email)  # ← 1 query
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({
                # "email": ["Email is not registered"]
                "email": ["Email no registrado."]
            })
        
        # Password verification (in-memory, no additional DB queries)
        if not user.check_password(password):  # ← 0 extra queries
            raise serializers.ValidationError({
                # "password": ["Incorrect password"]
                "password": ["Contraseña incorrecta."]
            })
        
        # Return the authenticated user to be accessed in the view after .is_valid()
        return {"user": user}
