from django.contrib import admin

from .models import (
    Inventory,
    InventoryAlert,
    InventoryReservation,
    InventoryTransaction,
)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        "warehouse",
        "product",
        "variant",
        "quantity_on_hand",
        "quantity_reserved",
        "available",
        "updated_at",
    )
    search_fields = ("warehouse__code", "product__sku", "product__name")
    list_filter = ("warehouse", "updated_at")

    @admin.display(description="Khả dụng")
    def available(self, obj):
        return obj.quantity_available


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_type",
        "warehouse",
        "product",
        "quantity",
        "quantity_before",
        "quantity_after",
        "created_at",
    )
    search_fields = ("product__sku", "reference_type", "note")
    list_filter = ("transaction_type", "warehouse", "created_at")
    readonly_fields = [field.name for field in InventoryTransaction._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(InventoryReservation)
class InventoryReservationAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "status", "expires_at")
    search_fields = ("order__code", "product__sku", "product__name")
    list_filter = ("status", "warehouse", "expires_at")


admin.site.register(InventoryAlert)
