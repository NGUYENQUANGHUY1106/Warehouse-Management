from django.db.models import Count, Sum
from rest_framework import viewsets
from rest_framework.response import Response

from apps.accounts.rbac import (
    StorePermission,
    get_active_membership,
    requested_store_id,
)
from apps.inventory.models import Inventory
from apps.orders.models import Order
from apps.stock_in.models import StockIn


class ReportViewSet(viewsets.ViewSet):
    permission_classes = [StorePermission]
    permission_map = {"list": "report.view"}

    def list(self, request):
        membership = get_active_membership(request)
        store_id = (
            requested_store_id(request)
            if request.user.is_superuser
            else membership.store_id
        )
        orders = Order.objects.all()
        stock_ins = StockIn.objects.all()
        inventory = Inventory.objects.all()
        if store_id:
            orders = orders.filter(store_id=store_id)
            stock_ins = stock_ins.filter(store_id=store_id)
            inventory = inventory.filter(warehouse__store_id=store_id)

        order_totals = orders.aggregate(
            order_count=Count("id"),
            revenue=Sum("total"),
        )
        stock_in_totals = stock_ins.aggregate(stock_in_value=Sum("total"))
        inventory_totals = inventory.aggregate(
            sku_count=Count("id"),
            quantity_on_hand=Sum("quantity_on_hand"),
            quantity_reserved=Sum("quantity_reserved"),
        )
        return Response(
            {
                **order_totals,
                **stock_in_totals,
                **inventory_totals,
            }
        )
