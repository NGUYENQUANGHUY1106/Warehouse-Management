from django.contrib import admin

from .models import StockOut, StockOutItem


class StockOutItemInline(admin.TabularInline):
    model = StockOutItem
    extra = 0


@admin.register(StockOut)
class StockOutAdmin(admin.ModelAdmin):
    list_display = ("code", "store", "warehouse", "reason", "status", "created_at")
    search_fields = ("code", "customer__name", "note")
    list_filter = ("store", "warehouse", "reason", "status")
    inlines = (StockOutItemInline,)
