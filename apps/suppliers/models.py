from django.db import models
from django.db.models import Q

from apps.core.models import UUIDModel


class Supplier(UUIDModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Hoạt động"
        INACTIVE = "INACTIVE", "Ngừng hoạt động"

    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="suppliers",
    )
    code = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=500, blank=True)
    tax_code = models.CharField(max_length=50, blank=True)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
    )
    note = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["store", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["store", "code"],
                name="uq_supplier_store_code",
            ),
            models.CheckConstraint(
                check=Q(rating__gte=0) & Q(rating__lte=5),
                name="ck_supplier_rating_range",
            ),
        ]
        indexes = [models.Index(fields=["store", "status", "is_active"])]
        verbose_name = "Nhà cung cấp"
        verbose_name_plural = "Nhà cung cấp"

    @property
    def debt(self):
        latest = self.debt_transactions.order_by("-created_at").first()
        return latest.balance_after if latest else 0

    def __str__(self):
        return f"{self.code} - {self.name}"


class SupplierDebtTransaction(UUIDModel):
    class TransactionType(models.TextChoices):
        PURCHASE = "PURCHASE", "Mua hàng"
        PAYMENT = "PAYMENT", "Thanh toán"
        ADJUSTMENT = "ADJUSTMENT", "Điều chỉnh"

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="debt_transactions",
    )
    stock_in = models.ForeignKey(
        "stock_in.StockIn",
        on_delete=models.PROTECT,
        related_name="debt_transactions",
        null=True,
        blank=True,
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        db_index=True,
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    balance_after = models.DecimalField(max_digits=18, decimal_places=2)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="supplier_debt_transactions",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=Q(amount__gt=0),
                name="ck_supplier_debt_amount_positive",
            ),
            models.CheckConstraint(
                check=Q(balance_after__gte=0),
                name="ck_supplier_debt_balance_nonnegative",
            ),
        ]
        indexes = [
            models.Index(fields=["supplier", "created_at"]),
            models.Index(fields=["transaction_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.supplier.code} - {self.transaction_type} - {self.amount}"
