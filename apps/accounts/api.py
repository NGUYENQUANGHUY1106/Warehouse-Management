from django.contrib.auth import authenticate, get_user_model
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit_logs.models import AuditLog
from apps.audit_logs.services import record_audit

from .models import Permission, Role, StoreMember, User
from .rbac import (
    StorePermission,
    StorePermissionViewMixin,
    StoreQuerySetMixin,
    active_memberships,
    get_active_membership,
    permission_codes,
)
from .serializers import (
    PermissionSerializer,
    RoleSerializer,
    StoreMemberSerializer,
    UserSerializer,
)

UserModel = get_user_model()


class AuthView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def post(self, request):
        self.permission_classes = [AllowAny]
        identifier = request.data.get("username") or request.data.get("email")
        password = request.data.get("password")
        username = identifier
        if identifier and "@" in identifier:
            username = (
                UserModel.objects.filter(email__iexact=identifier)
                .values_list("username", flat=True)
                .first()
            )
        user = authenticate(request, username=username, password=password)
        if not user or user.status != User.Status.ACTIVE:
            return Response(
                {"detail": "Thông tin đăng nhập không hợp lệ."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token, _ = Token.objects.get_or_create(user=user)
        membership = active_memberships(user).first()
        if membership:
            request.session["active_store_id"] = str(membership.store_id)
        if membership:
            record_audit(
                store=membership.store,
                user=user,
                action=AuditLog.Action.LOGIN,
                module="accounts",
                instance=user,
                new_data={"authenticated": True},
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
        return Response(
            {
                "token": token.key,
                "user": UserSerializer(user).data,
                "active_store": str(membership.store_id) if membership else None,
                "role": membership.role.name if membership else None,
                "permissions": sorted(
                    permission_codes(user, membership.store_id if membership else None)
                ),
            }
        )

    def delete(self, request):
        membership = get_active_membership(request)
        if membership:
            record_audit(
                store=membership.store,
                user=request.user,
                action=AuditLog.Action.LOGOUT,
                module="accounts",
                instance=request.user,
                new_data={"authenticated": False, "source": "api"},
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return super().get_permissions()


class UserViewSet(StoreQuerySetMixin, viewsets.ModelViewSet):
    queryset = UserModel.objects.all().select_related("profile").distinct()
    serializer_class = UserSerializer
    permission_classes = [StorePermission]
    store_lookup = "store_memberships__store"
    permission_map = {
        "list": "user.view",
        "retrieve": "user.view",
        "create": "user.manage",
        "update": "user.manage",
        "partial_update": "user.manage",
        "destroy": "user.manage",
    }
    search_fields = ["username", "email", "first_name", "last_name", "phone"]
    ordering_fields = ["username", "email", "created_at"]

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()


class RoleViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = Role.objects.all().prefetch_related("permissions")
    serializer_class = RoleSerializer
    permission_map = {
        "list": "role.view",
        "retrieve": "role.view",
        "create": "role.manage",
        "update": "role.manage",
        "partial_update": "role.manage",
        "destroy": "role.manage",
    }
    search_fields = ["name", "description", "store__name"]
    ordering_fields = ["name", "created_at"]


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [StorePermission]
    permission_map = {"list": "role.view", "retrieve": "role.view"}
    search_fields = ["code", "module", "name"]


class StoreMemberViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = StoreMember.objects.select_related("store", "user", "role")
    serializer_class = StoreMemberSerializer
    permission_map = {
        "list": "user.view",
        "retrieve": "user.view",
        "create": "user.manage",
        "update": "user.manage",
        "partial_update": "user.manage",
        "destroy": "user.manage",
    }
    search_fields = ["user__username", "user__email", "store__name", "role__name"]
