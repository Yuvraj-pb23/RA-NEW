from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Tiny read-only snapshot of a User.
    Used as a nested field inside other serializers (e.g., assigned_by).
    Never exposes password or sensitive fields.
    """

    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "display_name"]
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    """
    Full user profile — used on GET /api/v1/users/<id>/ and GET /api/v1/auth/me/.
    """

    display_name = serializers.CharField(read_only=True)
    is_platform_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone",
            "display_name",
            "is_platform_admin",
            "is_active",
            "is_staff",
            "date_joined",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_staff",
            "date_joined",
            "updated_at",
            "display_name",
            "is_platform_admin",
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Used by POST /api/v1/users/ (admin creates a new user).
    Accepts plain-text password and hashes it via set_password().
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ["email", "full_name", "phone", "password", "password_confirm"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Used by PATCH /api/v1/users/<id>/.
    Cannot change email or password through this serializer.
    Password change gets its own dedicated endpoint.
    """

    class Meta:
        model = User
        fields = ["full_name", "phone", "is_active"]
