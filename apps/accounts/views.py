from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from apps.audit_logs.models import AuditLog
from apps.audit_logs.services import record_audit

from .models import User
from .rbac import active_memberships, redirect_authenticated_user


@redirect_authenticated_user
def login_view(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()
        password = request.POST.get("password", "")
        username = identifier
        if "@" in identifier:
            username = (
                User.objects.filter(email__iexact=identifier)
                .values_list("username", flat=True)
                .first()
            )
        user = authenticate(request, username=username, password=password)
        if not user or user.status != User.Status.ACTIVE:
            messages.error(request, "Email/tên đăng nhập hoặc mật khẩu không đúng.")
        else:
            membership = active_memberships(user).first()
            if not membership and not user.is_superuser:
                messages.error(request, "Tài khoản chưa được cấp quyền vào gian hàng.")
            else:
                login(request, user)
                if membership:
                    request.session["active_store_id"] = str(membership.store_id)
                    record_audit(
                        store=membership.store,
                        user=user,
                        action=AuditLog.Action.LOGIN,
                        module="accounts",
                        instance=user,
                        new_data={"authenticated": True, "source": "web"},
                        ip_address=request.META.get("REMOTE_ADDR"),
                        user_agent=request.META.get("HTTP_USER_AGENT", ""),
                    )
                next_url = request.POST.get("next") or request.GET.get("next")
                if not url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    next_url = "dashboard"
                return redirect(next_url)
    return render(request, "login.html")


def logout_view(request):
    if request.method != "POST":
        return redirect("dashboard" if request.user.is_authenticated else "login")
    if request.user.is_authenticated:
        membership = active_memberships(request.user).first()
        if membership:
            record_audit(
                store=membership.store,
                user=request.user,
                action=AuditLog.Action.LOGOUT,
                module="accounts",
                instance=request.user,
                new_data={"authenticated": False, "source": "web"},
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
    logout(request)
    messages.success(request, "Bạn đã đăng xuất an toàn.")
    return redirect("login")


@login_required
def switch_store_view(request):
    if request.method != "POST":
        return redirect("dashboard")
    membership = (
        active_memberships(request.user)
        .filter(store_id=request.POST.get("store"))
        .first()
    )
    if not membership and not request.user.is_superuser:
        messages.error(request, "Bạn không phải thành viên của gian hàng này.")
        return redirect("dashboard")
    if membership:
        request.session["active_store_id"] = str(membership.store_id)
    next_url = request.POST.get("next")
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = "dashboard"
    return redirect(next_url)
