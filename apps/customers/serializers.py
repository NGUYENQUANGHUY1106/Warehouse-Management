from rest_framework import serializers

from .models import Customer, CustomerGroup


class CustomerGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerGroup
        fields = "__all__"


class CustomerSerializer(serializers.ModelSerializer):
    total_orders = serializers.IntegerField(read_only=True)
    total_spent = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Customer
        fields = "__all__"

    def validate(self, attrs):
        store = attrs.get("store", getattr(self.instance, "store", None))
        group = attrs.get(
            "customer_group",
            getattr(self.instance, "customer_group", None),
        )
        if store and group and group.store_id != store.id:
            raise serializers.ValidationError(
                {"customer_group": "Nhóm khách phải thuộc cùng gian hàng."}
            )
        return attrs
