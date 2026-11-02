from rest_framework import viewsets

from apps.accounts.rbac import StorePermissionViewMixin

from .models import Brand, Category, Product, ProductVariant
from .serializers import (
    BrandSerializer,
    CategorySerializer,
    ProductSerializer,
    ProductVariantSerializer,
)

PRODUCT_PERMISSIONS = {
    "list": "product.view",
    "retrieve": "product.view",
    "create": "product.create",
    "update": "product.update",
    "partial_update": "product.update",
    "destroy": "product.delete",
}


class CategoryViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = Category.objects.select_related("store", "parent")
    serializer_class = CategorySerializer
    permission_map = PRODUCT_PERMISSIONS
    search_fields = ["name", "slug", "store__name"]
    ordering_fields = ["name", "created_at"]


class BrandViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = Brand.objects.select_related("store")
    serializer_class = BrandSerializer
    permission_map = PRODUCT_PERMISSIONS
    search_fields = ["name", "slug", "store__name"]


class ProductViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = Product.objects.select_related(
        "store", "category", "brand"
    ).prefetch_related("images", "variants")
    serializer_class = ProductSerializer
    permission_map = PRODUCT_PERMISSIONS
    search_fields = ["sku", "barcode", "name", "store__name"]
    ordering_fields = ["sku", "name", "selling_price", "created_at"]


class ProductVariantViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = ProductVariant.objects.select_related("product", "product__store")
    serializer_class = ProductVariantSerializer
    store_lookup = "product__store"
    validated_store_source = "product.store"
    permission_map = PRODUCT_PERMISSIONS
    search_fields = ["sku", "barcode", "name", "product__name"]
