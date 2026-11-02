from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import UUIDModel


class Order(UUIDModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Chờ xác nhận"
        CONFIRMED = "CONFIRMED", "Đã xác nhận"
        PROCESSING = "PROCESSING", "Đang xử lý"
        PACKING = "PACKING", "Đang đóng gói"
        SHIPPING = "SHIPPING", "Đang giao"
        COMPLETED = "COMPLETED", "Hoàn thành"
        CANCELLED = "CANCELLED", "Đã hủy"
        RETURNED = "RETURNED", "Hoàn trả"

    class PaymentStatus(models.TextChoices):
        UNPAID = "UNPAID", "Chưa thanh toán"
        PAID = "PAID", "Đã thanh toán"
        PARTIAL = "PARTIAL", "Thanh toán một phần"
        REFUNDED = "REFUNDED", "Đã hoàn tiền"

    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="orders",
        null=True,
        blank=True,
    )
    code = models.CharField(max_length=50, db_index=True)
    order_date = models.DateTimeField(default=timezone.now, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        db_index=True,
    )
    subtotal = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
    )
    tax = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="created_orders",
    )

    class Meta:
        ordering = ["-order_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["store", "code"],
                name="uq_order_store_code",
            ),
            models.CheckConstraint(
                check=Q(subtotal__gte=0),
                name="ck_order_subtotal_nonnegative",
            ),
            models.CheckConstraint(
                check=Q(discount__gte=0),
                name="ck_order_discount_nonnegative",
            ),
            models.CheckConstraint(
                check=Q(shipping_fee__gte=0),
                name="ck_order_shipping_nonnegative",
            ),
            models.CheckConstraint(
                check=Q(tax__gte=0),
                name="ck_order_tax_nonnegative",
            ),
            models.CheckConstraint(
                check=Q(total__gte=0),
                name="ck_order_total_nonnegative",
            ),
        ]
        indexes = [
            models.Index(fields=["store", "status", "order_date"]),
            models.Index(fields=["customer", "order_date"]),
            models.Index(fields=["payment_status", "order_date"]),
        ]
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"

    def clean(self):
        if self.warehouse_id and self.warehouse.store_id != self.store_id:
            raise ValidationError("Kho và đơn hàng phải cùng gian hàng.")
        if self.customer_id and self.customer.store_id != self.store_id:
            raise ValidationError("Khách hàng và đơn hàng phải cùng gian hàng.")

    def __str__(self):
        return f"{self.code} - {self.get_status_display()}"


class OrderItem(UUIDModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="order_items",
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    discount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(quantity__gt=0),
                name="ck_order_item_quantity_positive",
            ),
            models.CheckConstraint(
                check=Q(unit_price__gte=0),
                name="ck_order_item_price_nonnegative",
            ),
            models.CheckConstraint(
                check=Q(discount__gte=0),
                name="ck_order_item_discount_nonnegative",
            ),
            models.CheckConstraint(
                check=Q(subtotal__gte=0),
                name="ck_order_item_subtotal_nonnegative",
            ),
            models.UniqueConstraint(
                fields=["order", "product"],
                condition=Q(variant__isnull=True),
                name="uq_order_item_no_variant",
            ),
            models.UniqueConstraint(
                fields=["order", "product", "variant"],
                condition=Q(variant__isnull=False),
                name="uq_order_item_variant",
            ),
        ]

    def clean(self):
        if self.product_id and self.order_id:
            if self.product.store_id != self.order.store_id:
                raise ValidationError("Sản phẩm phải thuộc gian hàng.")
        if self.variant_id and self.variant.product_id != self.product_id:
            raise ValidationError("Biến thể không thuộc sản phẩm.")

    def __str__(self):
        return f"{self.order.code} - {self.product.sku} x {self.quantity}"


class OrderStatusHistory(UUIDModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    old_status = models.CharField(
        max_length=20,
        choices=Order.Status.choices,
        blank=True,
    )
    new_status = models.CharField(max_length=20, choices=Order.Status.choices)
    changed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="order_status_changes",
    )
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["order", "created_at"])]

    def __str__(self):
        return f"{self.order.code}: {self.old_status} -> {self.new_status}"
