from django.db import models

from apps.core.models import UUIDModel


class Store(UUIDModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Đang hoạt động"
        INACTIVE = "INACTIVE", "Tạm ngưng"
        SUSPENDED = "SUSPENDED", "Bị khóa"

    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to="stores/logos/", blank=True)
    banner = models.ImageField(upload_to="stores/banners/", blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=500, blank=True)
    province = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    ward = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    tax_code = models.CharField(max_length=50, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["status", "created_at"])]
        verbose_name = "Gian hàng"
        verbose_name_plural = "Gian hàng"

    def __str__(self):
        return f"{self.code} - {self.name}"
