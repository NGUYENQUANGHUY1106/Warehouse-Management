from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.audit_logs.models import AuditLog
from apps.audit_logs.services import record_audit
from apps.inventory.models import InventoryTransaction
from apps.inventory.services import get_inventory_for_update

from .models import StockIn, StockInItem


@transaction.atomic
def create_stock_in(*, data, items, created_by):
    stock_in = StockIn(created_by=created_by, **data)
    stock_in.full_clean()
    stock_in.save()
    subtotal = Decimal("0")
    for item_data in items:
        quantity = item_data["quantity"]
        unit_cost = Decimal(item_data["unit_cost"])
        line_subtotal = quantity * unit_cost
        item = StockInItem(
            stock_in=stock_in,
            subtotal=line_subtotal,
            **item_data,
        )
        item.full_clean()
        item.save()
        subtotal += line_subtotal
    stock_in.subtotal = subtotal
    stock_in.total = subtotal - stock_in.discount + stock_in.tax
    stock_in.full_clean()
    stock_in.save(update_fields=["subtotal", "total", "updated_at"])
    return stock_in


@transaction.atomic
def complete_stock_in(*, stock_in, approved_by):
    stock_in = (
        StockIn.objects.select_for_update()
        .prefetch_related("items__product", "items__variant")
        .get(pk=stock_in.pk)
    )
    if stock_in.status == StockIn.Status.COMPLETED:
        return stock_in
    if stock_in.status == StockIn.Status.CANCELLED:
        raise ValidationError("Không thể hoàn tất phiếu đã hủy.")
    if not stock_in.items.exists():
        raise ValidationError("Phiếu nhập phải có ít nhất một sản phẩm.")
    old_status = stock_in.status

    for item in stock_in.items.all():
        inventory = get_inventory_for_update(
            stock_in.warehouse,
            item.product,
            item.variant,
        )
        quantity_before = inventory.quantity_on_hand
        inventory.quantity_on_hand += item.quantity
        inventory.save(update_fields=["quantity_on_hand", "updated_at"])
        InventoryTransaction.objects.create(
            warehouse=stock_in.warehouse,
            product=item.product,
            variant=item.variant,
            transaction_type=InventoryTransaction.TransactionType.STOCK_IN,
            quantity=item.quantity,
            quantity_before=quantity_before,
            quantity_after=inventory.quantity_on_hand,
            reference_type="StockIn",
            reference_id=stock_in.id,
            note=f"Hoàn tất phiếu nhập {stock_in.code}",
            created_by=approved_by,
        )

    stock_in.status = StockIn.Status.COMPLETED
    stock_in.approved_by = approved_by
    stock_in.save(update_fields=["status", "approved_by", "updated_at"])
    record_audit(
        store=stock_in.store,
        user=approved_by,
        action=AuditLog.Action.STOCK_IN,
        module="stock_in",
        instance=stock_in,
        old_data={"status": old_status},
        new_data={"status": stock_in.status},
    )
    return stock_in
