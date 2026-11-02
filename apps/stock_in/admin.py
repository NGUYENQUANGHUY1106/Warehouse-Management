from django.contrib import admin

from .models import StockIn, StockInItem


class StockInItemInline(admin.TabularInline):
    model = StockInItem
    extra = 0


@admin.register(StockIn)
class StockInAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "store",
        "warehouse",
        "supplier",
        "stock_in_date",
        "total",
        "status",
    )
    search_fields = ("code", "supplier__code", "supplier__name")
    list_filter = ("store", "warehouse", "status", "stock_in_date")
    inlines = (StockInItemInline,)
