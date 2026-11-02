from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.rbac import StorePermissionViewMixin

from .models import StockOut
from .serializers import StockOutSerializer
from .services import complete_stock_out


class StockOutViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = StockOut.objects.select_related(
        "store",
        "warehouse",
        "customer",
        "destination_warehouse",
        "created_by",
        "approved_by",
    ).prefetch_related("items")
    serializer_class = StockOutSerializer
    permission_map = {
        "list": "stockout.view",
        "retrieve": "stockout.view",
        "create": "stockout.create",
        "update": "stockout.create",
        "partial_update": "stockout.create",
        "destroy": "stockout.create",
        "complete": "stockout.complete",
    }
    search_fields = ["code", "customer__name", "note"]
    ordering_fields = ["code", "created_at"]

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        try:
            stock_out = complete_stock_out(
                stock_out=self.get_object(),
                approved_by=request.user,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return Response(self.get_serializer(stock_out).data)
