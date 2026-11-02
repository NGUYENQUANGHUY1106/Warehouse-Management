from rest_framework import viewsets

from apps.accounts.rbac import StorePermissionViewMixin

from .models import Supplier, SupplierDebtTransaction
from .serializers import (
    SupplierDebtTransactionSerializer,
    SupplierSerializer,
)

SUPPLIER_PERMISSIONS = {
    "list": "supplier.view",
    "retrieve": "supplier.view",
    "create": "supplier.manage",
    "update": "supplier.manage",
    "partial_update": "supplier.manage",
    "destroy": "supplier.manage",
}


class SupplierViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = Supplier.objects.select_related("store")
    serializer_class = SupplierSerializer
    permission_map = SUPPLIER_PERMISSIONS
    search_fields = ["code", "name", "contact_name", "phone", "email"]
    ordering_fields = ["code", "name", "rating", "created_at"]


class SupplierDebtTransactionViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = SupplierDebtTransaction.objects.select_related(
        "supplier",
        "stock_in",
        "created_by",
    )
    serializer_class = SupplierDebtTransactionSerializer
    store_lookup = "supplier__store"
    validated_store_source = "supplier.store"
    permission_map = SUPPLIER_PERMISSIONS
    search_fields = ["supplier__code", "supplier__name", "note"]

    def perform_create(self, serializer):
        self._check_write_store(serializer)
        serializer.save(created_by=self.request.user)
