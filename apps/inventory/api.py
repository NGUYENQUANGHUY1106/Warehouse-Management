from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.rbac import StorePermissionViewMixin

from .models import (
    Inventory,
    InventoryAlert,
    InventoryReservation,
    InventoryTransaction,
)
from .serializers import (
    InventoryAlertSerializer,
    InventoryReservationSerializer,
    InventorySerializer,
    InventoryTransactionSerializer,
)
from .services import adjust_inventory


class InventoryViewSet(StorePermissionViewMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Inventory.objects.select_related(
        "warehouse",
        "product",
        "variant",
    )
    serializer_class = InventorySerializer
    store_lookup = "warehouse__store"
    permission_map = {
        "list": "inventory.view",
        "retrieve": "inventory.view",
        "adjust": "inventory.adjust",
    }
    search_fields = [
        "warehouse__code",
        "warehouse__name",
        "product__sku",
        "product__name",
        "variant__sku",
    ]
    ordering_fields = ["quantity_on_hand", "quantity_reserved", "updated_at"]

    @action(detail=True, methods=["post"])
    def adjust(self, request, pk=None):
        inventory = self.get_object()
        try:
            quantity_after = int(request.data["quantity_after"])
        except (KeyError, TypeError, ValueError) as exc:
            raise serializers.ValidationError(
                {"quantity_after": "Cần nhập số nguyên hợp lệ."}
            ) from exc
        try:
            inventory = adjust_inventory(
                warehouse=inventory.warehouse,
                product=inventory.product,
                variant=inventory.variant,
                quantity_after=quantity_after,
                note=request.data.get("note", ""),
                user=request.user,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return Response(self.get_serializer(inventory).data)


class InventoryTransactionViewSet(
    StorePermissionViewMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = InventoryTransaction.objects.select_related(
        "warehouse",
        "product",
        "variant",
        "created_by",
    )
    serializer_class = InventoryTransactionSerializer
    store_lookup = "warehouse__store"
    permission_map = {"list": "inventory.view", "retrieve": "inventory.view"}
    search_fields = ["product__sku", "reference_type", "note"]


class InventoryReservationViewSet(
    StorePermissionViewMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = InventoryReservation.objects.select_related(
        "order",
        "warehouse",
        "product",
        "variant",
    )
    serializer_class = InventoryReservationSerializer
    store_lookup = "warehouse__store"
    permission_map = {"list": "inventory.view", "retrieve": "inventory.view"}
    search_fields = ["order__code", "product__sku", "product__name"]


class InventoryAlertViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = InventoryAlert.objects.select_related(
        "inventory",
        "inventory__product",
    )
    serializer_class = InventoryAlertSerializer
    store_lookup = "inventory__warehouse__store"
    validated_store_source = "inventory.warehouse.store"
    permission_map = {
        "list": "inventory.view",
        "retrieve": "inventory.view",
        "create": "inventory.adjust",
        "update": "inventory.adjust",
        "partial_update": "inventory.adjust",
        "destroy": "inventory.adjust",
    }
    search_fields = ["message", "inventory__product__sku"]
