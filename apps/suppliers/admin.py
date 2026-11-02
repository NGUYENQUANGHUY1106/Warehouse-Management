from django.contrib import admin

from .models import Supplier, SupplierDebtTransaction


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "store", "phone", "rating", "status")
    search_fields = ("code", "name", "contact_name", "phone", "email")
    list_filter = ("store", "status", "rating", "is_active")


@admin.register(SupplierDebtTransaction)
class SupplierDebtTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "supplier",
        "transaction_type",
        "amount",
        "balance_after",
        "created_at",
    )
    search_fields = ("supplier__code", "supplier__name", "note")
    list_filter = ("transaction_type", "created_at")
