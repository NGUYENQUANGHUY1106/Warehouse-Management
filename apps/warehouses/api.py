from rest_framework import viewsets

from apps.accounts.rbac import StorePermissionViewMixin

from .models import Warehouse
from .serializers import WarehouseSerializer


class WarehouseViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = Warehouse.objects.select_related("store", "manager")
    serializer_class = WarehouseSerializer
    permission_map = {
        "list": "warehouse.view",
        "retrieve": "warehouse.view",
        "create": "warehouse.manage",
        "update": "warehouse.manage",
        "partial_update": "warehouse.manage",
        "destroy": "warehouse.manage",
    }
    search_fields = ["code", "name", "address", "store__name"]
    ordering_fields = ["code", "name", "created_at"]
