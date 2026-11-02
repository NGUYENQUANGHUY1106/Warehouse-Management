from django.db import models

from apps.core.models import UUIDModel


class Notification(UUIDModel):
    class Type(models.TextChoices):
        LOW_STOCK = "LOW_STOCK", "Sắp hết hàng"
        NEW_ORDER = "NEW_ORDER", "Đơn hàng mới"
        ORDER_CANCELLED = "ORDER_CANCELLED", "Đơn hàng bị hủy"
        SYSTEM = "SYSTEM", "Hệ thống"

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="notifications",
    )
    type = models.CharField(max_length=30, choices=Type.choices, db_index=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "created_at"]),
            models.Index(fields=["store", "type", "created_at"]),
        ]
        verbose_name = "Thông báo"
        verbose_name_plural = "Thông báo"

    def __str__(self):
        return f"{self.user} - {self.title}"
