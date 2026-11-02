from rest_framework import viewsets

from apps.accounts.rbac import StorePermissionViewMixin

from .models import Customer, CustomerGroup
from .serializers import CustomerGroupSerializer, CustomerSerializer

CUSTOMER_PERMISSIONS = {
    "list": "customer.view",
    "retrieve": "customer.view",
    "create": "customer.manage",
    "update": "customer.manage",
    "partial_update": "customer.manage",
    "destroy": "customer.manage",
}


class CustomerViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = Customer.objects.select_related("store", "customer_group")
    serializer_class = CustomerSerializer
    permission_map = CUSTOMER_PERMISSIONS
    search_fields = ["code", "name", "phone", "email"]
    ordering_fields = ["code", "name", "created_at"]


class CustomerGroupViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = CustomerGroup.objects.select_related("store")
    serializer_class = CustomerGroupSerializer
    permission_map = CUSTOMER_PERMISSIONS
    search_fields = ["name", "store__name"]
