from django.contrib import admin

from .models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "phone", "email", "status", "created_at")
    search_fields = ("code", "name", "phone", "email", "tax_code")
    list_filter = ("status", "province", "created_at")
