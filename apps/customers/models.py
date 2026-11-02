from decimal import Decimal

from django.db import models
from django.db.models import Q, Sum

from apps.core.models import UUIDModel


class CustomerGroup(UUIDModel):
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="customer_groups",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store", "name"],
                name="uq_customer_group_store_name",
            )
        ]

    def __str__(self):
        return f"{self.store.code} - {self.name}"


class Customer(UUIDModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Hoạt động"
        INACTIVE = "INACTIVE", "Ngừng hoạt động"
        BLOCKED = "BLOCKED", "Bị chặn"

    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="customers",
    )
    code = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30, blank=True, db_index=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=500, blank=True)
    province = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    ward = models.CharField(max_length=100, blank=True)
    customer_group = models.ForeignKey(
        CustomerGroup,
        on_delete=models.PROTECT,
        related_name="customers",
        null=True,
        blank=True,
    )
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
                name="uq_customer_store_code",
            ),
            models.UniqueConstraint(
                fields=["store", "phone"],
                condition=~Q(phone=""),
                name="uq_customer_store_phone",
            ),
        ]
        indexes = [models.Index(fields=["store", "status", "is_active"])]
        verbose_name = "Khách hàng"
        verbose_name_plural = "Khách hàng"

    @property
    def total_orders(self):
        return self.orders.exclude(status="CANCELLED").count()

    @property
    def total_spent(self):
        result = self.orders.filter(status="COMPLETED").aggregate(total=Sum("total"))
        return result["total"] or Decimal("0")

    def __str__(self):
        return f"{self.code} - {self.name}"
