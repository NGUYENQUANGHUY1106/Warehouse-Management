from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.core.models import UUIDModel


class CatalogStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Hoạt động"
    INACTIVE = "INACTIVE", "Ngừng hoạt động"
    ARCHIVED = "ARCHIVED", "Lưu trữ"


class Category(UUIDModel):
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="categories",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="children",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True)
    status = models.CharField(
        max_length=20,
        choices=CatalogStatus.choices,
        default=CatalogStatus.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ["store", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["store", "slug"],
                name="uq_category_store_slug",
            )
        ]
        indexes = [models.Index(fields=["store", "status"])]
        verbose_name = "Danh mục"
        verbose_name_plural = "Danh mục"

    def clean(self):
        if self.parent and self.parent.store_id != self.store_id:
            raise ValidationError("Danh mục cha phải thuộc cùng gian hàng.")

    def __str__(self):
        return f"{self.store.code} - {self.name}"


class Brand(UUIDModel):
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="brands",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    logo = models.ImageField(upload_to="brands/", blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=CatalogStatus.choices,
        default=CatalogStatus.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ["store", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["store", "slug"],
                name="uq_brand_store_slug",
            )
        ]
        verbose_name = "Thương hiệu"
        verbose_name_plural = "Thương hiệu"

    def __str__(self):
        return f"{self.store.code} - {self.name}"


class Product(UUIDModel):
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="products",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )
    sku = models.CharField(max_length=100, db_index=True)
    barcode = models.CharField(max_length=100, blank=True, db_index=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=50, default="cái")
    cost_price = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    selling_price = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
    )
    min_stock_level = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=CatalogStatus.choices,
        default=CatalogStatus.ACTIVE,
        db_index=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["store", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["store", "sku"],
                name="uq_product_store_sku",
            ),
            models.UniqueConstraint(
                fields=["store", "slug"],
                name="uq_product_store_slug",
            ),
            models.UniqueConstraint(
                fields=["store", "barcode"],
                condition=~Q(barcode=""),
                name="uq_product_store_barcode",
            ),
            models.CheckConstraint(
                check=Q(cost_price__gte=0),
                name="ck_product_cost_nonnegative",
            ),
            models.CheckConstraint(
                check=Q(selling_price__gte=0),
                name="ck_product_price_nonnegative",
            ),
        ]
        indexes = [
            models.Index(fields=["store", "status", "is_active"]),
            models.Index(fields=["store", "name"]),
        ]
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"

    def clean(self):
        if self.category_id and self.category.store_id != self.store_id:
            raise ValidationError("Danh mục phải thuộc cùng gian hàng.")
        if self.brand_id and self.brand.store_id != self.store_id:
            raise ValidationError("Thương hiệu phải thuộc cùng gian hàng.")

    def __str__(self):
        return f"{self.sku} - {self.name}"


class ProductImage(UUIDModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="products/")
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=Q(is_primary=True),
                name="uq_product_primary_image",
            )
        ]

    def __str__(self):
        return f"Ảnh {self.product} #{self.sort_order}"


class ProductVariant(UUIDModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="variants",
    )
    sku = models.CharField(max_length=100, db_index=True)
    barcode = models.CharField(max_length=100, blank=True, db_index=True)
    name = models.CharField(max_length=255)
    cost_price = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    selling_price = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
    )
    status = models.CharField(
        max_length=20,
        choices=CatalogStatus.choices,
        default=CatalogStatus.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ["product", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "sku"],
                name="uq_variant_product_sku",
            ),
            models.UniqueConstraint(
                fields=["product", "barcode"],
                condition=~Q(barcode=""),
                name="uq_variant_product_barcode",
            ),
            models.CheckConstraint(
                check=Q(cost_price__gte=0),
                name="ck_variant_cost_nonnegative",
            ),
            models.CheckConstraint(
                check=Q(selling_price__gte=0),
                name="ck_variant_price_nonnegative",
            ),
        ]
        verbose_name = "Biến thể sản phẩm"
        verbose_name_plural = "Biến thể sản phẩm"

    def __str__(self):
        return f"{self.sku} - {self.product.name} - {self.name}"


class Attribute(UUIDModel):
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="product_attributes",
    )
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store", "name"],
                name="uq_attribute_store_name",
            )
        ]

    def __str__(self):
        return f"{self.store.code} - {self.name}"


class AttributeValue(UUIDModel):
    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        related_name="values",
    )
    value = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["attribute", "value"],
                name="uq_attribute_value",
            )
        ]

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class VariantAttribute(UUIDModel):
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="attribute_links",
    )
    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.PROTECT,
        related_name="variant_links",
    )
    value = models.ForeignKey(
        AttributeValue,
        on_delete=models.PROTECT,
        related_name="variant_links",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["variant", "attribute"],
                name="uq_variant_attribute",
            )
        ]

    def clean(self):
        if self.value_id and self.value.attribute_id != self.attribute_id:
            raise ValidationError("Giá trị không thuộc thuộc tính đã chọn.")
        if (
            self.variant_id
            and self.attribute_id
            and self.variant.product.store_id != self.attribute.store_id
        ):
            raise ValidationError("Thuộc tính phải thuộc cùng gian hàng.")

    def __str__(self):
        return f"{self.variant} - {self.attribute.name}: {self.value.value}"
