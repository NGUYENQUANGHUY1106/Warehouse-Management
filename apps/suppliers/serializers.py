from rest_framework import serializers

from .models import Supplier, SupplierDebtTransaction


class SupplierSerializer(serializers.ModelSerializer):
    debt = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Supplier
        fields = "__all__"


class SupplierDebtTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierDebtTransaction
        fields = "__all__"
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]
