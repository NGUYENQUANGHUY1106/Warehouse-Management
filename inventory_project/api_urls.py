from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.accounts.api import (
    AuthView,
    PermissionViewSet,
    RoleViewSet,
    StoreMemberViewSet,
    UserViewSet,
)
from apps.audit_logs.api import AuditLogViewSet
from apps.customers.api import CustomerGroupViewSet, CustomerViewSet
from apps.inventory.api import (
    InventoryAlertViewSet,
    InventoryReservationViewSet,
    InventoryTransactionViewSet,
    InventoryViewSet,
)
from apps.notifications.api import NotificationViewSet
from apps.orders.api import OrderViewSet
from apps.payments.api import PaymentViewSet
from apps.products.api import (
    BrandViewSet,
    CategoryViewSet,
    ProductVariantViewSet,
    ProductViewSet,
)
from apps.reports.api import ReportViewSet
from apps.stock_in.api import StockInViewSet
from apps.stock_out.api import StockOutViewSet
from apps.stores.api import StoreViewSet
from apps.suppliers.api import SupplierDebtTransactionViewSet, SupplierViewSet
from apps.warehouses.api import WarehouseViewSet

router = DefaultRouter()
router.register("stores", StoreViewSet)
router.register("products", ProductViewSet)
router.register("product-variants", ProductVariantViewSet)
router.register("categories", CategoryViewSet)
router.register("brands", BrandViewSet)
router.register("warehouses", WarehouseViewSet)
router.register("inventory", InventoryViewSet)
router.register("inventory-transactions", InventoryTransactionViewSet)
router.register("inventory-reservations", InventoryReservationViewSet)
router.register("inventory-alerts", InventoryAlertViewSet)
router.register("stock-in", StockInViewSet)
router.register("stock-out", StockOutViewSet)
router.register("orders", OrderViewSet)
router.register("payments", PaymentViewSet)
router.register("customers", CustomerViewSet)
router.register("customer-groups", CustomerGroupViewSet)
router.register("suppliers", SupplierViewSet)
router.register("supplier-debts", SupplierDebtTransactionViewSet)
router.register("users", UserViewSet)
router.register("roles", RoleViewSet)
router.register("permissions", PermissionViewSet)
router.register("store-members", StoreMemberViewSet)
router.register("reports", ReportViewSet, basename="reports")
router.register("audit-logs", AuditLogViewSet)
router.register("notifications", NotificationViewSet, basename="notifications")

urlpatterns = [path("auth/", AuthView.as_view(), name="api-auth")]
urlpatterns += router.urls
