import uuid

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel


class User(AbstractUser, TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Hoạt động"
        INACTIVE = "INACTIVE", "Ngừng hoạt động"
        SUSPENDED = "SUSPENDED", "Bị khóa"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    avatar = models.ImageField(upload_to="users/avatars/", blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ["username"]
        indexes = [models.Index(fields=["email", "status"])]
        verbose_name = "Người dùng"
        verbose_name_plural = "Người dùng"

    def __str__(self):
        return self.get_full_name() or self.username


class UserProfile(UUIDModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    job_title = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"Hồ sơ {self.user}"


class Permission(UUIDModel):
    code = models.CharField(max_length=100, unique=True, db_index=True)
    module = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=150)

    class Meta:
        ordering = ["module", "code"]
        verbose_name = "Quyền"
        verbose_name_plural = "Quyền"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Role(UUIDModel):
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="roles",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(default=False)
    permissions = models.ManyToManyField(
        Permission,
        related_name="roles",
        blank=True,
    )

    class Meta:
        ordering = ["store", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["store", "name"],
                name="uq_role_store_name",
            )
        ]
        verbose_name = "Vai trò"
        verbose_name_plural = "Vai trò"

    def __str__(self):
        return f"{self.store.code} - {self.name}"


class StoreMember(UUIDModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Hoạt động"
        INACTIVE = "INACTIVE", "Ngừng hoạt động"
        INVITED = "INVITED", "Đã mời"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="store_memberships",
    )
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="members",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="members",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["store", "user"]
        constraints = [
            models.UniqueConstraint(
                fields=["store", "user"],
                name="uq_store_member_user",
            )
        ]
        indexes = [models.Index(fields=["store", "status"])]
        verbose_name = "Thành viên gian hàng"
        verbose_name_plural = "Thành viên gian hàng"

    def clean(self):
        if self.role_id and self.store_id and self.role.store_id != self.store_id:
            raise ValidationError("Vai trò phải thuộc cùng gian hàng.")

    def __str__(self):
        return f"{self.user} @ {self.store} ({self.role.name})"
