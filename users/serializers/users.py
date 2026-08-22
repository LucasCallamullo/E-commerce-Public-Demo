from django.contrib.auth import get_user_model
from rest_framework import serializers

CustomUser = get_user_model()


class UserMeSerializer(serializers.ModelSerializer):
    """
    Serializer for updating the authenticated user's own profile.

    Only allows editing personal and non-sensitive fields.
    Fields not provided or sent as empty strings are ignored.
    """

    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "cellphone",
            "province",
            "address",
            "dni",
        ]
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
            "dni": {"required": False},
            "cellphone": {"required": False},
            "address": {"required": False},
            "province": {"required": False},
        }

    def validate(self, attrs):
        """
        Remove empty string values so they do not overwrite existing data.
        """
        return {k: v for k, v in attrs.items() if v != ""}


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and retrieving user data.

    The 'role' field is read-only and managed by the system.
    """

    class Meta:
        model = CustomUser
        # devuelve json y recibe json para validar de estos campos
        fields = ["id", "role", "first_name", "last_name", "email", "dni", "cellphone"]
        
        # solo lee estos campos evitando usar otros valores que no sean por defecto
        read_only_fields = ["id", "role"]

    def validate_email(self, value):
        """
        Ensure the email address is unique across users.
        """
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ese email ya está registrado.")
        return value

