from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Order, OrderItem, OrderStatusHistory
from .services import create_order


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"
        read_only_fields = ["id", "order", "subtotal", "created_at", "updated_at"]


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = [
            "id",
            "status",
            "payment_status",
            "subtotal",
            "total",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        items = validated_data.pop("items")
        try:
            return create_order(
                data=validated_data,
                items=items,
                created_by=self.context["request"].user,
                reserve=True,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def update(self, instance, validated_data):
        raise serializers.ValidationError(
            "Không sửa trực tiếp đơn hàng; hãy dùng action vòng đời đơn."
        )
