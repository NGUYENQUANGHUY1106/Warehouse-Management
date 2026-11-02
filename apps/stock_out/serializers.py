from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import StockOut, StockOutItem
from .services import create_stock_out


class StockOutItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockOutItem
        fields = "__all__"
        read_only_fields = ["id", "stock_out", "subtotal", "created_at", "updated_at"]


class StockOutSerializer(serializers.ModelSerializer):
    items = StockOutItemSerializer(many=True)
    total = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = StockOut
        fields = "__all__"
        read_only_fields = [
            "id",
            "status",
            "created_by",
            "approved_by",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        items = validated_data.pop("items")
        try:
            return create_stock_out(
                data=validated_data,
                items=items,
                created_by=self.context["request"].user,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def update(self, instance, validated_data):
        raise serializers.ValidationError(
            "Không sửa trực tiếp phiếu xuất; hãy hủy và tạo phiếu mới."
        )
