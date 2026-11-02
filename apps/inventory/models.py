from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from apps.core.models import UUIDModel


class Inventory(UUIDModel):
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.PROTECT,
        related_name="inventory_records",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="inventory_records",
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="inventory_records",
        null=True,
        blank=True,
    )
    quantity_on_hand = models.PositiveIntegerField(default=0)
    quantity_reserved = models.PositiveIntegerField(default=0)
    min_stock_level = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["warehouse", "product", "variant"]
        constraints = [
            models.UniqueConstraint(
                fields=["warehouse", "product"],
                condition=Q(variant__isnull=True),
                name="uq_inventory_without_variant",
            ),
            models.UniqueConstraint(
                fields=["warehouse", "product", "variant"],
                condition=Q(variant__isnull=False),
                name="uq_inventory_with_variant",
            ),
            models.CheckConstraint(
                check=Q(quantity_on_hand__gte=0),
                name="ck_inventory_on_hand_nonnegative",
            ),
            models.CheckConstraint(
                check=Q(quantity_reserved__gte=0),
                name="ck_inventory_reserved_nonnegative",
            ),
            models.CheckConstraint(
                check=Q(quantity_reserved__lte=F("quantity_on_hand")),
                name="ck_inventory_reserved_lte_on_hand",
            ),
        ]
        indexes = [
            models.Index(fields=["warehouse", "product"]),
            models.Index(fields=["product", "variant"]),
        ]
        verbose_name = "Tồn kho"
        verbose_name_plural = "Tồn kho"

    @property
    def quantity_available(self):
        return self.quantity_on_hand - self.quantity_reserved

    def clean(self):
        if self.product_id and self.warehouse_id:
            if self.product.store_id != self.warehouse.store_id:
                raise ValidationError("Sản phẩm và kho phải cùng gian hàng.")
        if self.variant_id and self.variant.product_id != self.product_id:
            raise ValidationError("Biến thể không thuộc sản phẩm đã chọn.")
        if self.quantity_reserved > self.quantity_on_hand:
            raise ValidationError("Số lượng giữ không được vượt tồn vật lý.")

    def __str__(self):
        variant = f" / {self.variant.name}" if self.variant else ""
        return f"{self.warehouse.code} - {self.product.sku}{variant}"


class InventoryTransaction(UUIDModel):
    class TransactionType(models.TextChoices):
        STOCK_IN = "STOCK_IN", "Nhập kho"
        STOCK_OUT = "STOCK_OUT", "Xuất kho"
        SALE = "SALE", "Bán hàng"
        CANCEL = "CANCEL", "Hủy"
        RETURN = "RETURN", "Hoàn trả"
        ADJUSTMENT = "ADJUSTMENT", "Điều chỉnh"
        TRANSFER_IN = "TRANSFER_IN", "Chuyển vào"
        TRANSFER_OUT = "TRANSFER_OUT", "Chuyển ra"
        RESERVE = "RESERVE", "Giữ hàng"
        RELEASE = "RELEASE", "Nhả giữ hàng"

    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.PROTECT,
        related_name="inventory_transactions",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="inventory_transactions",
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="inventory_transactions",
        null=True,
        blank=True,
    )
    transaction_type = models.CharField(
        max_length=30,
        choices=TransactionType.choices,
        db_index=True,
    )
    quantity = models.PositiveIntegerField()
    quantity_before = models.PositiveIntegerField()
    quantity_after = models.PositiveIntegerField()
    reference_type = models.CharField(max_length=100, blank=True, db_index=True)
    reference_id = models.UUIDField(null=True, blank=True, db_index=True)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="inventory_transactions",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=Q(quantity__gt=0),
                name="ck_inventory_tx_quantity_positive",
            )
        ]
        indexes = [
            models.Index(fields=["warehouse", "product", "created_at"]),
            models.Index(fields=["transaction_type", "created_at"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]
        verbose_name = "Giao dịch kho"
        verbose_name_plural = "Giao dịch kho"

    def __str__(self):
        return f"{self.transaction_type} - {self.product.sku} - {self.quantity}"


class InventoryReservation(UUIDModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Đang giữ"
        RELEASED = "RELEASED", "Đã nhả"
        CONSUMED = "CONSUMED", "Đã sử dụng"
        EXPIRED = "EXPIRED", "Hết hạn"

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="reservations",
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["expires_at"]
        constraints = [
            models.CheckConstraint(
                check=Q(quantity__gt=0),
                name="ck_reservation_quantity_positive",
            ),
            models.UniqueConstraint(
                fields=["order", "warehouse", "product"],
                condition=Q(status="ACTIVE", variant__isnull=True),
                name="uq_active_reservation_no_variant",
            ),
            models.UniqueConstraint(
                fields=["order", "warehouse", "product", "variant"],
                condition=Q(status="ACTIVE", variant__isnull=False),
                name="uq_active_reservation_variant",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "expires_at"]),
            models.Index(fields=["warehouse", "product", "variant"]),
        ]
        verbose_name = "Giữ tồn kho"
        verbose_name_plural = "Giữ tồn kho"

    def __str__(self):
        return f"{self.order.code} - {self.product.sku} - {self.quantity}"


class InventoryAlert(UUIDModel):
    class AlertType(models.TextChoices):
        LOW_STOCK = "LOW_STOCK", "Sắp hết hàng"
        OUT_OF_STOCK = "OUT_OF_STOCK", "Hết hàng"

    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    alert_type = models.CharField(
        max_length=30,
        choices=AlertType.choices,
        db_index=True,
    )
    message = models.CharField(max_length=500)
    is_resolved = models.BooleanField(default=False, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["inventory", "alert_type"],
                condition=Q(is_resolved=False),
                name="uq_unresolved_inventory_alert",
            )
        ]
        indexes = [models.Index(fields=["alert_type", "is_resolved"])]

    def __str__(self):
        return f"{self.alert_type} - {self.inventory}"
