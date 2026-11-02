from django.core.exceptions import PermissionDenied
from rest_framework import viewsets

from apps.accounts.rbac import StorePermissionViewMixin

from .models import Store
from .serializers import StoreSerializer


class StoreViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    store_lookup = "pk"
    permission_map = {
        "list": "store.view",
        "retrieve": "store.view",
        "create": "store.manage",
        "update": "store.manage",
        "partial_update": "store.manage",
        "destroy": "store.manage",
    }
    search_fields = ["code", "name", "phone", "email", "tax_code"]
    ordering_fields = ["code", "name", "created_at"]

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            raise PermissionDenied("Chỉ quản trị hệ thống được tạo gian hàng mới.")
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()
