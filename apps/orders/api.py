from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.rbac import StorePermissionViewMixin

from .models import Order
from .serializers import OrderSerializer
from .services import cancel_order, complete_order, confirm_order


class OrderViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = Order.objects.select_related(
        "store",
        "warehouse",
        "customer",
        "created_by",
    ).prefetch_related("items", "status_history", "payments", "reservations")
    serializer_class = OrderSerializer
    permission_map = {
        "list": "order.view",
        "retrieve": "order.view",
        "create": "order.create",
        "update": "order.update",
        "partial_update": "order.update",
        "destroy": "order.cancel",
        "confirm": "order.update",
        "complete": "order.complete",
        "cancel": "order.cancel",
    }
    search_fields = ["code", "customer__name", "customer__phone", "note"]
    ordering_fields = ["code", "order_date", "total", "created_at"]

    def _run_action(self, service, request):
        try:
            order = service(order=self.get_object(), user=request.user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        return self._run_action(confirm_order, request)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        return self._run_action(complete_order, request)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._run_action(cancel_order, request)
