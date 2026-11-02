from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Permission, Role, StoreMember, User, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["id", "job_title", "bio", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        validators=[validate_password],
    )
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone",
            "avatar",
            "status",
            "is_active",
            "is_staff",
            "last_login",
            "created_at",
            "updated_at",
            "profile",
        ]
        read_only_fields = ["id", "last_login", "created_at", "updated_at"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def validate_is_staff(self, value):
        request = self.context.get("request")
        if request and not request.user.is_superuser:
            raise serializers.ValidationError(
                "Chỉ quản trị hệ thống được thay đổi quyền truy cập Django Admin."
            )
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=["password", "updated_at"])
        return instance


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = "__all__"


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"


class StoreMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreMember
        fields = "__all__"

    def validate(self, attrs):
        store = attrs.get("store", getattr(self.instance, "store", None))
        role = attrs.get("role", getattr(self.instance, "role", None))
        if store and role and role.store_id != store.id:
            raise serializers.ValidationError(
                {"role": "Vai trò phải thuộc cùng gian hàng."}
            )
        return attrs
