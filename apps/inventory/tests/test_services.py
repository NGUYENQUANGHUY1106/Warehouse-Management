from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.audit_logs.models import AuditLog
from apps.customers.models import Customer
from apps.orders.services import complete_order, create_order
from apps.products.models import Category, Product
from apps.stock_out.models import StockOut
from apps.stock_out.services import complete_stock_out, create_stock_out
from apps.stores.models import Store
from apps.warehouses.models import Warehouse

from ..models import Inventory, InventoryReservation
from ..services import release_expired_reservations


class InventoryServiceTests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(code="TEST", name="Test Store")
        self.user = User.objects.create_user(
            username="tester",
            email="tester@example.com",
            password="test-password-123",
        )
        self.warehouse = Warehouse.objects.create(
            store=self.store,
            code="WH1",
            name="Main Warehouse",
        )
        self.category = Category.objects.create(
            store=self.store,
            name="Test Category",
            slug="test-category",
        )
        self.product = Product.objects.create(
            store=self.store,
            category=self.category,
            sku="SKU-1",
            name="Test Product",
            slug="test-product",
            cost_price=Decimal("50.00"),
            selling_price=Decimal("100.00"),
        )
        self.customer = Customer.objects.create(
            store=self.store,
            code="CUS-1",
            name="Test Customer",
        )
        self.inventory = Inventory.objects.create(
            warehouse=self.warehouse,
            product=self.product,
            quantity_on_hand=5,
        )

    def create_reserved_order(self, code="ORDER-1", quantity=2):
        return create_order(
            data={
                "store": self.store,
                "warehouse": self.warehouse,
                "customer": self.customer,
                "code": code,
            },
            items=[
                {
                    "product": self.product,
                    "variant": None,
                    "quantity": quantity,
                    "unit_price": self.product.selling_price,
                    "discount": 0,
                }
            ],
            created_by=self.user,
        )

    def test_order_reserves_then_consumes_inventory(self):
        order = self.create_reserved_order()
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity_on_hand, 5)
        self.assertEqual(self.inventory.quantity_reserved, 2)

        complete_order(order=order, user=self.user)

        self.inventory.refresh_from_db()
        reservation = order.reservations.get()
        self.assertEqual(self.inventory.quantity_on_hand, 3)
        self.assertEqual(self.inventory.quantity_reserved, 0)
        self.assertEqual(
            reservation.status,
            InventoryReservation.Status.CONSUMED,
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.ORDER_STATUS_CHANGE,
                object_id=order.id,
            ).exists()
        )

    def test_stock_out_cannot_exceed_available_inventory(self):
        stock_out = create_stock_out(
            data={
                "store": self.store,
                "warehouse": self.warehouse,
                "code": "OUT-1",
                "reason": StockOut.Reason.INTERNAL,
            },
            items=[
                {
                    "product": self.product,
                    "variant": None,
                    "quantity": 6,
                    "unit_price": self.product.selling_price,
                }
            ],
            created_by=self.user,
        )

        with self.assertRaisesMessage(
            ValidationError,
            "Số lượng xuất vượt quá số lượng tồn kho hiện tại.",
        ):
            complete_stock_out(stock_out=stock_out, approved_by=self.user)

        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity_on_hand, 5)

    def test_expired_reservation_is_released(self):
        order = self.create_reserved_order()
        reservation = order.reservations.get()
        InventoryReservation.objects.filter(pk=reservation.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )

        released = release_expired_reservations()

        reservation.refresh_from_db()
        self.inventory.refresh_from_db()
        self.assertEqual(released, 1)
        self.assertEqual(reservation.status, InventoryReservation.Status.EXPIRED)
        self.assertEqual(self.inventory.quantity_reserved, 0)

    def test_audit_log_is_immutable(self):
        order = self.create_reserved_order()
        audit_log = AuditLog.objects.filter(object_id=order.id).first()
        self.assertIsNotNone(audit_log)

        with self.assertRaises(ValidationError):
            audit_log.delete()
        with self.assertRaises(ValidationError):
            AuditLog.objects.filter(pk=audit_log.pk).update(module="changed")
