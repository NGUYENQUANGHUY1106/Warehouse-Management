from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.core.models import UUIDModel


class StockIn(UUIDModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Nháp"
        PENDING = "PENDING", "Chờ duyệt"
        COMPLETED = "COMPLETED", "Hoàn thành"
        CANCELLED = "CANCELLED", "Đã hủy"

    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="stock_ins",
    )
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.PROTECT,
        related_name="stock_ins",
    )
    supplier = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.PROTECT,
        related_name="stock_ins",
    )
    code = models.CharField(max_length=50, db_index=True)
    stock_in_date = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    subtotal = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="created_stock_ins",
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="approved_stock_ins",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-stock_in_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["store", "code"],
                name="uq_stock_in_store_code",
            ),
            models.CheckConstraint(
                check=Q(subtotal__gte=0),
                name="ck_stock_in_subtotal_nonnegative",
            ),
            models.CheckConstraint(
                check=Q(discount__gte=0),
                name="ck_stock_in_discount_nonnegative",
            ),
            models.CheckConstraint(
                check=Q(tax__gte=0),
                name="ck_stock_in_tax_nonnegative",
            ),
            models.CheckConstraint(
                check=Q(total__gte=0),
                name="ck_stock_in_total_nonnegative",
            ),
        ]
        indexes = [
            models.Index(fields=["store", "status", "stock_in_date"]),
            models.Index(fields=["supplier", "stock_in_date"]),
        ]
        verbose_name = "Phiếu nhập"
        verbose_name_plural = "Phiếu nhập"

    def clean(self):
        if self.warehouse_id and self.warehouse.store_id != self.store_id:
            raise ValidationError("Kho nhập phải thuộc gian hàng.")
        if self.supplier_id and self.supplier.store_id != self.store_id:
            raise ValidationError("Nhà cung cấp phải thuộc gian hàng.")

    def __str__(self):
        return f"{self.code} - {self.supplier.name}"


class StockInItem(UUIDModel):
    stock_in = models.ForeignKey(
        StockIn,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="stock_in_items",
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="stock_in_items",
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2)
    subtotal = models.DecimalField(max_digits=18, decimal_places=2)
    note = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(quantity__gt=0),
                name="ck_stock_in_item_quantity_positive",
            ),
            models.CheckConstraint(
                check=Q(unit_cost__gte=0),
                name="ck_stock_in_item_cost_nonnegative",
            ),
            models.CheckConstraint(
                check=Q(subtotal__gte=0),
                name="ck_stock_in_item_subtotal_nonnegative",
            ),
            models.UniqueConstraint(
                fields=["stock_in", "product"],
                condition=Q(variant__isnull=True),
                name="uq_stock_in_item_no_variant",
            ),
            models.UniqueConstraint(
                fields=["stock_in", "product", "variant"],
                condition=Q(variant__isnull=False),
                name="uq_stock_in_item_variant",
            ),
        ]

    def clean(self):
        if self.product_id and self.stock_in_id:
            if self.product.store_id != self.stock_in.store_id:
                raise ValidationError("Sản phẩm phải thuộc gian hàng.")
        if self.variant_id and self.variant.product_id != self.product_id:
            raise ValidationError("Biến thể không thuộc sản phẩm.")

    def __str__(self):
        return f"{self.stock_in.code} - {self.product.sku} x {self.quantity}"
