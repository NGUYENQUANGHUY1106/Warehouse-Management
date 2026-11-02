from django.utils import timezone
from rest_framework import viewsets

from apps.accounts.rbac import StorePermissionViewMixin
from apps.audit_logs.models import AuditLog
from apps.audit_logs.services import record_audit

from .models import (
    Brand,
    CatalogStatus,
    Category,
    Product,
    ProductImage,
    ProductVariant,
)
from .serializers import (
    BrandSerializer,
    CategorySerializer,
    ProductImageSerializer,
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


def _audit_data(instance):
    return {
        "id": str(instance.pk),
        "name": str(getattr(instance, "name", instance)),
    }


class ProductAuditMixin:
    def _record(self, action, instance, old_data=None, new_data=None):
        store = getattr(instance, "store", None)
        if store is None and hasattr(instance, "product"):
            store = instance.product.store
        record_audit(
            store=store,
            user=self.request.user,
            action=action,
            module="products",
            instance=instance,
            old_data=old_data or {},
            new_data=new_data or {},
            ip_address=self.request.META.get("REMOTE_ADDR"),
            user_agent=self.request.META.get("HTTP_USER_AGENT", ""),
        )

    def perform_create(self, serializer):
        super().perform_create(serializer)
        self._record(
            AuditLog.Action.CREATE,
            serializer.instance,
            new_data=_audit_data(serializer.instance),
        )

    def perform_update(self, serializer):
        old_data = _audit_data(serializer.instance)
        super().perform_update(serializer)
        self._record(
            AuditLog.Action.UPDATE,
            serializer.instance,
            old_data=old_data,
            new_data=_audit_data(serializer.instance),
        )

    def perform_destroy(self, instance):
        self._record(
            AuditLog.Action.DELETE,
            instance,
            old_data=_audit_data(instance),
        )
        super().perform_destroy(instance)


class CategoryViewSet(
    ProductAuditMixin, StorePermissionViewMixin, viewsets.ModelViewSet
):
    queryset = Category.objects.select_related("store", "parent")
    serializer_class = CategorySerializer
    permission_map = PRODUCT_PERMISSIONS
    search_fields = ["name", "slug", "store__name"]
    ordering_fields = ["name", "created_at"]


class BrandViewSet(ProductAuditMixin, StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = Brand.objects.select_related("store")
    serializer_class = BrandSerializer
    permission_map = PRODUCT_PERMISSIONS
    search_fields = ["name", "slug", "store__name"]


class ProductViewSet(
    ProductAuditMixin, StorePermissionViewMixin, viewsets.ModelViewSet
):
    queryset = Product.objects.select_related(
        "store", "category", "brand"
    ).prefetch_related("images", "variants")
    serializer_class = ProductSerializer
    permission_map = PRODUCT_PERMISSIONS
    search_fields = ["sku", "barcode", "name", "store__name"]
    ordering_fields = ["sku", "name", "selling_price", "created_at"]

    def perform_destroy(self, instance):
        old_data = _audit_data(instance)
        instance.is_active = False
        instance.status = CatalogStatus.ARCHIVED
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["is_active", "status", "deleted_at", "updated_at"])
        self._record(
            AuditLog.Action.DELETE,
            instance,
            old_data=old_data,
            new_data={**_audit_data(instance), "is_active": False},
        )


class ProductImageViewSet(
    ProductAuditMixin,
    StorePermissionViewMixin,
    viewsets.ModelViewSet,
):
    queryset = ProductImage.objects.select_related("product", "product__store")
    serializer_class = ProductImageSerializer
    store_lookup = "product__store"
    validated_store_source = "product.store"
    permission_map = PRODUCT_PERMISSIONS
    search_fields = ["product__sku", "product__name"]


class ProductVariantViewSet(
    ProductAuditMixin,
    StorePermissionViewMixin,
    viewsets.ModelViewSet,
):
    queryset = ProductVariant.objects.select_related("product", "product__store")
    serializer_class = ProductVariantSerializer
    store_lookup = "product__store"
    validated_store_source = "product.store"
    permission_map = PRODUCT_PERMISSIONS
    search_fields = ["sku", "barcode", "name", "product__name"]
