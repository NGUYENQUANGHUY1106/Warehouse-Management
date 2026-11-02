from django.contrib import admin

from .models import (
    Attribute,
    AttributeValue,
    Brand,
    Category,
    Product,
    ProductImage,
    ProductVariant,
    VariantAttribute,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "name",
        "store",
        "category",
        "selling_price",
        "status",
        "is_active",
    )
    search_fields = ("sku", "barcode", "name", "store__name")
    list_filter = ("store", "category", "brand", "status", "is_active")
    inlines = (ProductImageInline, ProductVariantInline)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "parent", "status", "created_at")
    search_fields = ("name", "slug", "store__name")
    list_filter = ("store", "status")


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "status", "created_at")
    search_fields = ("name", "slug", "store__name")
    list_filter = ("store", "status")


admin.site.register(Attribute)
admin.site.register(AttributeValue)
admin.site.register(VariantAttribute)
