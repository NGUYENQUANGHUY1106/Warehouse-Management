from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import UUIDModel


class ImmutableAuditLogQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Audit Log là bất biến và không thể sửa.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("Audit Log là bất biến và không thể sửa.")

    def delete(self):
        raise ValidationError("Audit Log là bất biến và không thể xóa.")


class AuditLog(UUIDModel):
    class Action(models.TextChoices):
        CREATE = "CREATE", "Tạo mới"
        UPDATE = "UPDATE", "Cập nhật"
        DELETE = "DELETE", "Xóa"
        LOGIN = "LOGIN", "Đăng nhập"
        LOGOUT = "LOGOUT", "Đăng xuất"
        STOCK_IN = "STOCK_IN", "Nhập kho"
        STOCK_OUT = "STOCK_OUT", "Xuất kho"
        ORDER_STATUS_CHANGE = "ORDER_STATUS_CHANGE", "Đổi trạng thái đơn"
        INVENTORY_ADJUSTMENT = "INVENTORY_ADJUSTMENT", "Điều chỉnh kho"

    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="audit_logs",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="audit_logs",
        null=True,
        blank=True,
    )
    action = models.CharField(
        max_length=30,
        choices=Action.choices,
        db_index=True,
    )
    module = models.CharField(max_length=100, db_index=True)
    object_type = models.CharField(max_length=100, db_index=True)
    object_id = models.UUIDField(null=True, blank=True, db_index=True)
    object_repr = models.CharField(max_length=500, blank=True)
    old_data = models.JSONField(default=dict, blank=True)
    new_data = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    objects = ImmutableAuditLogQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["store", "created_at"]),
            models.Index(fields=["module", "action", "created_at"]),
            models.Index(fields=["object_type", "object_id"]),
        ]
        verbose_name = "Nhật ký hệ thống"
        verbose_name_plural = "Nhật ký hệ thống"

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Audit Log là bất biến và không thể sửa.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Audit Log là bất biến và không thể xóa.")

    def __str__(self):
        return f"{self.created_at} - {self.action} - {self.object_repr}"
