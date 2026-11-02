from rest_framework import serializers

from .models import Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = "__all__"

    def validate(self, attrs):
        store = attrs.get("store", getattr(self.instance, "store", None))
        manager = attrs.get("manager", getattr(self.instance, "manager", None))
        if store and manager and manager.store_id != store.id:
            raise serializers.ValidationError(
                {"manager": "Quản lý kho phải thuộc cùng gian hàng."}
            )
        return attrs
