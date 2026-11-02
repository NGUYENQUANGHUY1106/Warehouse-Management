from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import StockIn, StockInItem
from .services import create_stock_in


class StockInItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockInItem
        fields = "__all__"
        read_only_fields = ["id", "stock_in", "subtotal", "created_at", "updated_at"]


class StockInSerializer(serializers.ModelSerializer):
    items = StockInItemSerializer(many=True)

    class Meta:
        model = StockIn
        fields = "__all__"
        read_only_fields = [
            "id",
            "status",
            "subtotal",
            "total",
            "created_by",
            "approved_by",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        items = validated_data.pop("items")
        try:
            return create_stock_in(
                data=validated_data,
                items=items,
                created_by=self.context["request"].user,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def update(self, instance, validated_data):
        raise serializers.ValidationError(
            "Không sửa trực tiếp phiếu nhập; hãy hủy và tạo phiếu mới."
        )
