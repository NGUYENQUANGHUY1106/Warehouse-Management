from django import forms
from django.utils.text import slugify

from .models import (
    Brand,
    CatalogStatus,
    Category,
    Product,
    ProductImage,
    ProductVariant,
)


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "field")


class ProductForm(StyledModelForm):
    class Meta:
        model = Product
        fields = [
            "sku",
            "barcode",
            "name",
            "slug",
            "category",
            "brand",
            "description",
            "unit",
            "cost_price",
            "selling_price",
            "min_stock_level",
            "status",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, store, **kwargs):
        super().__init__(*args, **kwargs)
        self.store = store
        self.fields["slug"].required = False
        self.fields["category"].queryset = Category.objects.filter(
            store=store,
            status=CatalogStatus.ACTIVE,
        )
        self.fields["brand"].queryset = Brand.objects.filter(
            store=store,
            status=CatalogStatus.ACTIVE,
        )

    def clean_slug(self):
        return self.cleaned_data.get("slug") or slugify(
            self.cleaned_data.get("name", "")
        )


class CategoryForm(StyledModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "parent", "description", "image", "status"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, store, **kwargs):
        super().__init__(*args, **kwargs)
        self.store = store
        self.fields["slug"].required = False
        parents = Category.objects.filter(store=store).exclude(pk=self.instance.pk)
        self.fields["parent"].queryset = parents

    def clean_slug(self):
        return self.cleaned_data.get("slug") or slugify(
            self.cleaned_data.get("name", "")
        )


class BrandForm(StyledModelForm):
    class Meta:
        model = Brand
        fields = ["name", "slug", "logo", "description", "status"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, store, **kwargs):
        super().__init__(*args, **kwargs)
        self.store = store
        self.fields["slug"].required = False

    def clean_slug(self):
        return self.cleaned_data.get("slug") or slugify(
            self.cleaned_data.get("name", "")
        )


class ProductImageForm(StyledModelForm):
    class Meta:
        model = ProductImage
        fields = ["image", "is_primary", "sort_order"]


class ProductVariantForm(StyledModelForm):
    class Meta:
        model = ProductVariant
        fields = [
            "sku",
            "barcode",
            "name",
            "cost_price",
            "selling_price",
            "status",
        ]
