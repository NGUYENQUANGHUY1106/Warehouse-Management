from django.contrib import admin

from .models import Customer, CustomerGroup


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "store", "phone", "status", "is_active")
    search_fields = ("code", "name", "phone", "email")
    list_filter = ("store", "customer_group", "status", "is_active")


admin.site.register(CustomerGroup)
