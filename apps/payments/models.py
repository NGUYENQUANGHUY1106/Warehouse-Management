from django.db import models
from django.db.models import Q

from apps.core.models import UUIDModel


class Payment(UUIDModel):
    class Method(models.TextChoices):
        CASH = "CASH", "Tiền mặt"
        BANK_TRANSFER = "BANK_TRANSFER", "Chuyển khoản"
        COD = "COD", "Thanh toán khi nhận hàng"
        MOMO = "MOMO", "MoMo"
        VNPAY = "VNPAY", "VNPay"
        OTHER = "OTHER", "Khác"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Chờ xử lý"
        SUCCESS = "SUCCESS", "Thành công"
        FAILED = "FAILED", "Thất bại"
        REFUNDED = "REFUNDED", "Đã hoàn tiền"

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    method = models.CharField(max_length=30, choices=Method.choices, db_index=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    transaction_code = models.CharField(max_length=150, blank=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    paid_at = models.DateTimeField(null=True, blank=True, db_index=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=Q(amount__gt=0),
                name="ck_payment_amount_positive",
            ),
            models.UniqueConstraint(
                fields=["transaction_code"],
                condition=~Q(transaction_code=""),
                name="uq_payment_transaction_code",
            ),
        ]
        indexes = [
            models.Index(fields=["order", "status"]),
            models.Index(fields=["method", "created_at"]),
        ]
        verbose_name = "Thanh toán"
        verbose_name_plural = "Thanh toán"

    def __str__(self):
        return f"{self.order.code} - {self.get_method_display()} - {self.amount}"
