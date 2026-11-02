from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, IntegerField, Q, Sum
from django.db.models.deletion import ProtectedError
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.rbac import (
    get_active_membership,
    requested_store_id,
    store_permission_required,
)
from apps.audit_logs.models import AuditLog
from apps.audit_logs.services import record_audit
from apps.stores.models import Store

from .forms import (
    BrandForm,
    CategoryForm,
    ProductForm,
    ProductImageForm,
    ProductVariantForm,
)
from .models import (
    Brand,
    CatalogStatus,
    Category,
    Product,
    ProductImage,
    ProductVariant,
)


def _active_store(request):
    membership = get_active_membership(request)
    if membership:
        return membership.store
    if request.user.is_superuser:
        store_id = requested_store_id(request)
        store = (
            Store.objects.filter(pk=store_id).first()
            if store_id
            else Store.objects.first()
        )
        if store:
            return store
    raise PermissionDenied("Không tìm thấy gian hàng hoạt động.")


def _product_queryset(store):
    return (
        Product.objects.filter(store=store)
        .select_related("category", "brand")
        .prefetch_related("images", "variants")
        .annotate(
            total_stock=Coalesce(
                Sum("inventory_records__quantity_on_hand"),
                0,
                output_field=IntegerField(),
            )
        )
    )


def _snapshot(instance):
    fields = ("id", "sku", "name", "status", "is_active")
    return {
        field: str(getattr(instance, field))
        for field in fields
        if hasattr(instance, field)
    }


def _audit(request, action, instance, old_data=None, new_data=None):
    record_audit(
        store=_active_store(request),
        user=request.user,
        action=action,
        module="products",
        instance=instance,
        old_data=old_data or {},
        new_data=new_data or {},
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )


@store_permission_required("product.view")
def product_list_view(request):
    store = _active_store(request)
    base_queryset = _product_queryset(store)
    queryset = base_queryset
    search = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    status = request.GET.get("status", "")
    ordering = request.GET.get("ordering", "name")

    if search:
        queryset = queryset.filter(
            Q(sku__icontains=search)
            | Q(barcode__icontains=search)
            | Q(name__icontains=search)
        )
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    if status == "ACTIVE":
        queryset = queryset.filter(is_active=True, status=CatalogStatus.ACTIVE)
    elif status == "INACTIVE":
        queryset = queryset.filter(is_active=True, status=CatalogStatus.INACTIVE)
    elif status == "DELETED":
        queryset = queryset.filter(is_active=False)
    else:
        queryset = queryset.filter(is_active=True)

    ordering_map = {
        "name": "name",
        "-created_at": "-created_at",
        "selling_price": "selling_price",
        "-selling_price": "-selling_price",
        "stock": "total_stock",
        "-stock": "-total_stock",
    }
    queryset = queryset.order_by(ordering_map.get(ordering, "name"))
    page_obj = Paginator(queryset, 20).get_page(request.GET.get("page"))

    active_products = base_queryset.filter(
        is_active=True,
        status=CatalogStatus.ACTIVE,
    )
    context = {
        "page_obj": page_obj,
        "categories": Category.objects.filter(store=store),
        "total_products": base_queryset.filter(is_active=True).count(),
        "active_products": active_products.count(),
        "low_stock_products": active_products.filter(
            total_stock__gt=0,
            total_stock__lte=F("min_stock_level"),
        ).count(),
        "out_of_stock_products": active_products.filter(total_stock=0).count(),
        "filters": {
            "q": search,
            "category": category_id,
            "status": status,
            "ordering": ordering,
        },
    }
    return render(request, "products.html", context)


@store_permission_required("product.view")
def product_detail_view(request, pk):
    product = get_object_or_404(_product_queryset(_active_store(request)), pk=pk)
    return render(request, "product_detail.html", {"product": product})


@store_permission_required("product.create")
@transaction.atomic
def product_create_view(request):
    store = _active_store(request)
    product = Product(store=store)
    form = ProductForm(
        request.POST or None, request.FILES or None, store=store, instance=product
    )
    if request.method == "POST" and form.is_valid():
        product = form.save()
        _audit(request, AuditLog.Action.CREATE, product, new_data=_snapshot(product))
        messages.success(request, f"Đã tạo sản phẩm {product.name}.")
        return redirect("product_edit", pk=product.pk)
    return render(
        request,
        "product_form.html",
        {"form": form, "product": None, "page_title": "Thêm sản phẩm"},
    )


@store_permission_required("product.update")
@transaction.atomic
def product_edit_view(request, pk):
    store = _active_store(request)
    product = get_object_or_404(Product, pk=pk, store=store)
    old_data = _snapshot(product)
    form = ProductForm(
        request.POST or None,
        request.FILES or None,
        store=store,
        instance=product,
    )
    if request.method == "POST" and form.is_valid():
        product = form.save()
        _audit(
            request,
            AuditLog.Action.UPDATE,
            product,
            old_data=old_data,
            new_data=_snapshot(product),
        )
        messages.success(request, "Đã cập nhật sản phẩm.")
        return redirect("product_edit", pk=product.pk)
    return render(
        request,
        "product_form.html",
        {
            "form": form,
            "product": product,
            "image_form": ProductImageForm(),
            "variant_form": ProductVariantForm(),
            "page_title": "Cập nhật sản phẩm",
        },
    )


@store_permission_required("product.delete")
@transaction.atomic
def product_delete_view(request, pk):
    if request.method != "POST":
        return redirect("product_detail", pk=pk)
    product = get_object_or_404(Product, pk=pk, store=_active_store(request))
    old_data = _snapshot(product)
    product.is_active = False
    product.status = CatalogStatus.ARCHIVED
    product.deleted_at = timezone.now()
    product.save(update_fields=["is_active", "status", "deleted_at", "updated_at"])
    _audit(
        request,
        AuditLog.Action.DELETE,
        product,
        old_data=old_data,
        new_data=_snapshot(product),
    )
    messages.success(
        request, "Đã lưu trữ sản phẩm; lịch sử giao dịch vẫn được giữ nguyên."
    )
    return redirect("product_list")


@store_permission_required("product.update")
@transaction.atomic
def product_restore_view(request, pk):
    if request.method != "POST":
        return redirect("product_detail", pk=pk)
    product = get_object_or_404(Product, pk=pk, store=_active_store(request))
    old_data = _snapshot(product)
    product.is_active = True
    product.status = CatalogStatus.ACTIVE
    product.deleted_at = None
    product.save(update_fields=["is_active", "status", "deleted_at", "updated_at"])
    _audit(
        request,
        AuditLog.Action.UPDATE,
        product,
        old_data=old_data,
        new_data=_snapshot(product),
    )
    messages.success(request, "Đã khôi phục sản phẩm.")
    return redirect("product_edit", pk=product.pk)


@store_permission_required("product.update")
@transaction.atomic
def product_image_add_view(request, pk):
    product = get_object_or_404(Product, pk=pk, store=_active_store(request))
    if request.method != "POST":
        return redirect("product_edit", pk=pk)
    form = ProductImageForm(request.POST, request.FILES)
    if form.is_valid():
        image = form.save(commit=False)
        image.product = product
        if image.is_primary or not product.images.exists():
            product.images.update(is_primary=False)
            image.is_primary = True
        image.full_clean()
        image.save()
        _audit(
            request,
            AuditLog.Action.CREATE,
            image,
            new_data={"product": str(product.id), "primary": image.is_primary},
        )
        messages.success(request, "Đã thêm ảnh sản phẩm.")
    else:
        messages.error(request, "Ảnh không hợp lệ. Vui lòng kiểm tra lại file.")
    return redirect("product_edit", pk=pk)


@store_permission_required("product.update")
@transaction.atomic
def product_image_delete_view(request, pk, image_id):
    product = get_object_or_404(Product, pk=pk, store=_active_store(request))
    image = get_object_or_404(ProductImage, pk=image_id, product=product)
    if request.method == "POST":
        was_primary = image.is_primary
        _audit(
            request,
            AuditLog.Action.DELETE,
            image,
            old_data={"product": str(product.id)},
        )
        image.image.delete(save=False)
        image.delete()
        if was_primary:
            replacement = product.images.first()
            if replacement:
                replacement.is_primary = True
                replacement.save(update_fields=["is_primary", "updated_at"])
        messages.success(request, "Đã xóa ảnh sản phẩm.")
    return redirect("product_edit", pk=pk)


@store_permission_required("product.update")
@transaction.atomic
def product_variant_add_view(request, pk):
    product = get_object_or_404(Product, pk=pk, store=_active_store(request))
    if request.method != "POST":
        return redirect("product_edit", pk=pk)
    form = ProductVariantForm(request.POST)
    if form.is_valid():
        variant = form.save(commit=False)
        variant.product = product
        try:
            variant.full_clean()
            variant.save()
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        else:
            _audit(
                request, AuditLog.Action.CREATE, variant, new_data=_snapshot(variant)
            )
            messages.success(request, "Đã thêm biến thể.")
    else:
        messages.error(request, "Biến thể không hợp lệ hoặc SKU đã tồn tại.")
    return redirect("product_edit", pk=pk)


@store_permission_required("product.update")
@transaction.atomic
def product_variant_delete_view(request, pk, variant_id):
    product = get_object_or_404(Product, pk=pk, store=_active_store(request))
    variant = get_object_or_404(ProductVariant, pk=variant_id, product=product)
    if request.method == "POST":
        try:
            _audit(
                request, AuditLog.Action.DELETE, variant, old_data=_snapshot(variant)
            )
            variant.delete()
        except ProtectedError:
            messages.error(
                request, "Không thể xóa biến thể đã phát sinh tồn kho/giao dịch."
            )
        else:
            messages.success(request, "Đã xóa biến thể.")
    return redirect("product_edit", pk=pk)


@store_permission_required("product.view")
def catalog_view(request):
    store = _active_store(request)
    return render(
        request,
        "catalog.html",
        {
            "categories": Category.objects.filter(store=store).select_related("parent"),
            "brands": Brand.objects.filter(store=store),
        },
    )


def _catalog_form_view(request, model, form_class, template_title, pk=None):
    store = _active_store(request)
    instance = (
        get_object_or_404(model, pk=pk, store=store) if pk else model(store=store)
    )
    old_data = {"name": instance.name, "status": instance.status} if pk else {}
    form = form_class(
        request.POST or None,
        request.FILES or None,
        store=store,
        instance=instance,
    )
    if request.method == "POST" and form.is_valid():
        instance = form.save()
        _audit(
            request,
            AuditLog.Action.UPDATE if pk else AuditLog.Action.CREATE,
            instance,
            old_data=old_data,
            new_data={"name": instance.name, "status": instance.status},
        )
        messages.success(request, f"Đã lưu {template_title.lower()}.")
        return redirect("catalog")
    return render(
        request,
        "catalog_form.html",
        {"form": form, "page_title": template_title},
    )


@store_permission_required("product.create")
def category_create_view(request):
    return _catalog_form_view(request, Category, CategoryForm, "Thêm danh mục")


@store_permission_required("product.update")
def category_edit_view(request, pk):
    return _catalog_form_view(request, Category, CategoryForm, "Sửa danh mục", pk)


@store_permission_required("product.create")
def brand_create_view(request):
    return _catalog_form_view(request, Brand, BrandForm, "Thêm thương hiệu")


@store_permission_required("product.update")
def brand_edit_view(request, pk):
    return _catalog_form_view(request, Brand, BrandForm, "Sửa thương hiệu", pk)


@store_permission_required("product.delete")
def catalog_delete_view(request, entity, pk):
    if request.method != "POST":
        return redirect("catalog")
    store = _active_store(request)
    model = Category if entity == "category" else Brand if entity == "brand" else None
    if model is None:
        raise PermissionDenied("Loại dữ liệu không hợp lệ.")
    instance = get_object_or_404(model, pk=pk, store=store)
    try:
        _audit(
            request, AuditLog.Action.DELETE, instance, old_data={"name": instance.name}
        )
        instance.delete()
    except ProtectedError:
        messages.error(
            request, "Không thể xóa vì đang được sản phẩm hoặc dữ liệu khác sử dụng."
        )
    else:
        messages.success(request, "Đã xóa dữ liệu danh mục.")
    return redirect("catalog")
