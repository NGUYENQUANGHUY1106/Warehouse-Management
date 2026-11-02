from django.contrib import admin

from .models import Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "store", "manager", "status", "created_at")
    search_fields = ("code", "name", "address", "store__name")
    list_filter = ("store", "status", "province")
