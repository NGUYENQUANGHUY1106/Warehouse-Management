from rest_framework import serializers

from .models import (
    Inventory,
    InventoryAlert,
    InventoryReservation,
    InventoryTransaction,
)


class InventorySerializer(serializers.ModelSerializer):
    quantity_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Inventory
        fields = "__all__"


class InventoryTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryTransaction
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class InventoryReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryReservation
        fields = "__all__"
        read_only_fields = ["id", "status", "created_at", "updated_at"]


class InventoryAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryAlert
        fields = "__all__"
