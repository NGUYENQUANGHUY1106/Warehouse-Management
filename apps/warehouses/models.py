from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import UUIDModel


class Warehouse(UUIDModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Hoạt động"
        INACTIVE = "INACTIVE", "Ngừng hoạt động"

    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="warehouses",
    )
    code = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500, blank=True)
    province = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    ward = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    manager = models.ForeignKey(
        "accounts.StoreMember",
        on_delete=models.SET_NULL,
        related_name="managed_warehouses",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ["store", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["store", "code"],
                name="uq_warehouse_store_code",
            )
        ]
        indexes = [models.Index(fields=["store", "status"])]
        verbose_name = "Kho"
        verbose_name_plural = "Kho"

    def clean(self):
        if self.manager_id and self.manager.store_id != self.store_id:
            raise ValidationError("Quản lý kho phải là thành viên cùng gian hàng.")

    def __str__(self):
        return f"{self.store.code} - {self.code} - {self.name}"
