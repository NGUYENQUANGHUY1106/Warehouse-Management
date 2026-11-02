from django.contrib import admin

from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("old_status", "new_status", "changed_by", "note", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "store",
        "customer",
        "order_date",
        "total",
        "status",
        "payment_status",
    )
    search_fields = ("code", "customer__name", "customer__phone")
    list_filter = ("store", "warehouse", "status", "payment_status", "order_date")
    inlines = (OrderItemInline, OrderStatusHistoryInline)
