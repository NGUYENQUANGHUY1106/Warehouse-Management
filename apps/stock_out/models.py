from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.core.models import UUIDModel


class StockOut(UUIDModel):
    class Reason(models.TextChoices):
        SALE = "SALE", "Bán hàng"
        DAMAGED = "DAMAGED", "Hàng hỏng"
        TRANSFER = "TRANSFER", "Chuyển kho"
        INTERNAL = "INTERNAL", "Nội bộ"
        OTHER = "OTHER", "Khác"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Nháp"
        PENDING = "PENDING", "Chờ duyệt"
        COMPLETED = "COMPLETED", "Hoàn thành"
        CANCELLED = "CANCELLED", "Đã hủy"

    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="stock_outs",
    )
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.PROTECT,
        related_name="stock_outs",
    )
    code = models.CharField(max_length=50, db_index=True)
    reason = models.CharField(max_length=20, choices=Reason.choices, db_index=True)
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="stock_outs",
        null=True,
        blank=True,
    )
    destination_warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.PROTECT,
        related_name="incoming_transfers",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="created_stock_outs",
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="approved_stock_outs",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["store", "code"],
                name="uq_stock_out_store_code",
            )
        ]
        indexes = [
            models.Index(fields=["store", "status", "created_at"]),
            models.Index(fields=["reason", "created_at"]),
        ]
        verbose_name = "Phiếu xuất"
        verbose_name_plural = "Phiếu xuất"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    def clean(self):
        if self.warehouse_id and self.warehouse.store_id != self.store_id:
            raise ValidationError("Kho xuất phải thuộc gian hàng.")
        if self.customer_id and self.customer.store_id != self.store_id:
            raise ValidationError("Khách hàng phải thuộc gian hàng.")
        if self.reason == self.Reason.TRANSFER:
            if not self.destination_warehouse_id:
                raise ValidationError("Chuyển kho cần kho đích.")
            if self.destination_warehouse_id == self.warehouse_id:
                raise ValidationError("Kho đích phải khác kho xuất.")
            if self.destination_warehouse.store_id != self.store_id:
                raise ValidationError("Kho đích phải thuộc cùng gian hàng.")

    def __str__(self):
        return f"{self.code} - {self.get_reason_display()}"


class StockOutItem(UUIDModel):
    stock_out = models.ForeignKey(
        StockOut,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="stock_out_items",
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="stock_out_items",
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    subtotal = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(quantity__gt=0),
                name="ck_stock_out_item_quantity_positive",
            ),
            models.CheckConstraint(
                check=Q(unit_price__gte=0),
                name="ck_stock_out_item_price_nonnegative",
            ),
            models.CheckConstraint(
                check=Q(subtotal__gte=0),
                name="ck_stock_out_item_subtotal_nonnegative",
            ),
            models.UniqueConstraint(
                fields=["stock_out", "product"],
                condition=Q(variant__isnull=True),
                name="uq_stock_out_item_no_variant",
            ),
            models.UniqueConstraint(
                fields=["stock_out", "product", "variant"],
                condition=Q(variant__isnull=False),
                name="uq_stock_out_item_variant",
            ),
        ]

    def clean(self):
        if self.product_id and self.stock_out_id:
            if self.product.store_id != self.stock_out.store_id:
                raise ValidationError("Sản phẩm phải thuộc gian hàng.")
        if self.variant_id and self.variant.product_id != self.product_id:
            raise ValidationError("Biến thể không thuộc sản phẩm.")

    def __str__(self):
        return f"{self.stock_out.code} - {self.product.sku} x {self.quantity}"
