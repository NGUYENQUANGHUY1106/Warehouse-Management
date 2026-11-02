from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from rest_framework.permissions import BasePermission

from .models import StoreMember, User

SAFE_ACTIONS = {"list", "retrieve"}


def active_memberships(user):
    if not user.is_authenticated:
        return StoreMember.objects.none()
    return StoreMember.objects.filter(
        user=user,
        status=StoreMember.Status.ACTIVE,
        store__status="ACTIVE",
    ).select_related("store", "role")


def requested_store_id(request):
    header_store = request.headers.get("X-Store-ID")
    query_store = (
        request.query_params.get("store") if hasattr(request, "query_params") else None
    )
    form_store = request.POST.get("store") if request.method == "POST" else None
    session_store = request.session.get("active_store_id")
    return header_store or query_store or form_store or session_store


def get_active_membership(request):
    """Resolve and cache the user's membership for the current request."""
    if hasattr(request, "_storepro_membership"):
        return request._storepro_membership

    memberships = active_memberships(request.user)
    store_id = requested_store_id(request)
    membership = (
        memberships.filter(store_id=store_id).first()
        if store_id
        else memberships.first()
    )
    request._storepro_membership = membership
    if membership and hasattr(request, "session"):
        request.session["active_store_id"] = str(membership.store_id)
    return membership


def permission_codes(user, store_id=None):
    if not user.is_authenticated:
        return set()
    if user.is_superuser:
        return {"*"}
    memberships = active_memberships(user)
    if store_id:
        memberships = memberships.filter(store_id=store_id)
    return set(
        memberships.values_list("role__permissions__code", flat=True).exclude(
            role__permissions__code__isnull=True
        )
    )


def has_store_permission(user, code, store_id=None):
    if (
        not user.is_authenticated
        or not user.is_active
        or user.status != User.Status.ACTIVE
    ):
        return False
    if user.is_superuser:
        return True
    return code in permission_codes(user, store_id)


class StorePermission(BasePermission):
    """Check the permission code configured for the current ViewSet action."""

    message = "Bạn không có quyền thực hiện thao tác này trong gian hàng."

    def has_permission(self, request, view):
        user = request.user
        if (
            not user.is_authenticated
            or not user.is_active
            or user.status != User.Status.ACTIVE
        ):
            return False
        if user.is_superuser:
            return True

        membership = get_active_membership(request)
        if not membership:
            return False

        action = getattr(view, "action", request.method.lower())
        permission_map = getattr(view, "permission_map", {})
        code = permission_map.get(action)
        if code is None:
            code = getattr(view, "default_permission", None)
        if not code:
            return False
        return membership.role.permissions.filter(code=code).exists()


class StoreQuerySetMixin:
    """Restrict a ViewSet queryset and writes to the active store."""

    store_lookup = "store"
    validated_store_source = "store"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_superuser:
            store_id = requested_store_id(self.request)
            return self._filter_store(queryset, store_id) if store_id else queryset

        membership = get_active_membership(self.request)
        if not membership:
            return queryset.none()
        return self._filter_store(queryset, membership.store_id)

    def _filter_store(self, queryset, store_id):
        if self.store_lookup == "pk":
            return queryset.filter(pk=store_id)
        return queryset.filter(**{f"{self.store_lookup}_id": store_id})

    def _validated_store_id(self, validated_data):
        value = validated_data
        for part in self.validated_store_source.split("."):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = getattr(value, part, None)
            if value is None:
                return None
        return getattr(value, "pk", value)

    def _check_write_store(self, serializer):
        if self.request.user.is_superuser:
            return
        membership = get_active_membership(self.request)
        store_id = self._validated_store_id(serializer.validated_data)
        if not store_id and getattr(serializer, "instance", None) is not None:
            value = serializer.instance
            if self.store_lookup == "pk":
                store_id = value.pk
            else:
                for part in self.store_lookup.split("__"):
                    value = getattr(value, part, None)
                    if value is None:
                        break
                store_id = getattr(value, "pk", value)
        if not membership or not store_id or str(store_id) != str(membership.store_id):
            raise PermissionDenied("Không được ghi dữ liệu sang gian hàng khác.")

    def perform_create(self, serializer):
        self._check_write_store(serializer)
        serializer.save()

    def perform_update(self, serializer):
        self._check_write_store(serializer)
        serializer.save()


class StorePermissionViewMixin(StoreQuerySetMixin):
    permission_classes = [StorePermission]


def store_permission_required(code=None):
    """Protect HTML views using the same store role permissions as the API."""

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_active or request.user.status != User.Status.ACTIVE:
                raise PermissionDenied("Tài khoản đã bị vô hiệu hóa.")
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            membership = get_active_membership(request)
            if not membership:
                raise PermissionDenied("Tài khoản chưa thuộc gian hàng đang hoạt động.")
            if code and not membership.role.permissions.filter(code=code).exists():
                raise PermissionDenied("Bạn không có quyền mở trang này.")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def redirect_authenticated_user(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapped
