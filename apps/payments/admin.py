from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "method", "amount", "status", "paid_at")
    search_fields = ("order__code", "transaction_code", "note")
    list_filter = ("method", "status", "paid_at")
