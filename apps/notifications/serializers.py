from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        store = attrs.get("store", getattr(self.instance, "store", None))
        user = attrs.get("user", getattr(self.instance, "user", None))
        if (
            store
            and user
            and not user.store_memberships.filter(
                store=store,
                status="ACTIVE",
            ).exists()
        ):
            raise serializers.ValidationError(
                {"user": "Người nhận phải là thành viên đang hoạt động của gian hàng."}
            )
        return attrs
