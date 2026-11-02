from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.rbac import StorePermissionViewMixin

from .models import StockIn
from .serializers import StockInSerializer
from .services import complete_stock_in


class StockInViewSet(StorePermissionViewMixin, viewsets.ModelViewSet):
    queryset = StockIn.objects.select_related(
        "store",
        "warehouse",
        "supplier",
        "created_by",
        "approved_by",
    ).prefetch_related("items")
    serializer_class = StockInSerializer
    permission_map = {
        "list": "stockin.view",
        "retrieve": "stockin.view",
        "create": "stockin.create",
        "update": "stockin.create",
        "partial_update": "stockin.create",
        "destroy": "stockin.create",
        "complete": "stockin.complete",
    }
    search_fields = ["code", "supplier__code", "supplier__name", "note"]
    ordering_fields = ["code", "stock_in_date", "total", "created_at"]

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        try:
            stock_in = complete_stock_in(
                stock_in=self.get_object(),
                approved_by=request.user,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return Response(self.get_serializer(stock_in).data)
