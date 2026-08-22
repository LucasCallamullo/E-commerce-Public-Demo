

# users/serializers/docs.py
from rest_framework import serializers

class UserListResponseSerializer(serializers.Serializer):
    """
    Response schema for get users list.
    """
    id = serializers.IntegerField()
    role = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    dni = serializers.CharField(allow_null=True)
    cellphone = serializers.CharField(allow_null=True)


class UserRoleUpdateResponseSerializer(serializers.Serializer):
    """
    Response schema for user role update.
    """
    id = serializers.IntegerField()
    role = serializers.CharField()


class UserRoleUpdateRequestSerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=("admin", "seller", "buyer")
    )
