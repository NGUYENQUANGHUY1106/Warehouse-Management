from rest_framework import viewsets

from apps.accounts.rbac import StorePermissionViewMixin

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(StorePermissionViewMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("store", "user")
    serializer_class = AuditLogSerializer
    permission_map = {"list": "audit.view", "retrieve": "audit.view"}
    search_fields = [
        "module",
        "object_type",
        "object_repr",
        "user__username",
        "ip_address",
    ]
    ordering_fields = ["created_at", "action", "module"]
