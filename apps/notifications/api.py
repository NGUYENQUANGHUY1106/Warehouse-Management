from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.rbac import StorePermissionViewMixin

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = Notification.objects.select_related("user", "store")
    serializer_class = NotificationSerializer
    permission_map = {
        "list": "notification.view",
        "retrieve": "notification.view",
        "create": "notification.manage",
        "update": "notification.manage",
        "partial_update": "notification.manage",
        "destroy": "notification.manage",
        "mark_read": "notification.view",
    }
    search_fields = ["title", "message", "object_type"]
    ordering_fields = ["created_at", "is_read"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(user=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read", "updated_at"])
        return Response(self.get_serializer(notification).data)
