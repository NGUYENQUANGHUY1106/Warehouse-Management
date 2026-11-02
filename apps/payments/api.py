from rest_framework import viewsets

from apps.accounts.rbac import StorePermissionViewMixin

from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("order", "order__store")
    serializer_class = PaymentSerializer
    store_lookup = "order__store"
    validated_store_source = "order.store"
    permission_map = {
        "list": "payment.view",
        "retrieve": "payment.view",
        "create": "payment.manage",
        "update": "payment.manage",
        "partial_update": "payment.manage",
        "destroy": "payment.manage",
    }
    search_fields = ["order__code", "transaction_code", "note"]
    ordering_fields = ["amount", "paid_at", "created_at"]
