from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.audit_logs.models import AuditLog
from apps.audit_logs.services import record_audit
from apps.inventory.models import InventoryTransaction
from apps.inventory.services import get_inventory_for_update

from .models import StockOut, StockOutItem


@transaction.atomic
def create_stock_out(*, data, items, created_by):
    stock_out = StockOut(created_by=created_by, **data)
    stock_out.full_clean()
    stock_out.save()
    for item_data in items:
        quantity = item_data["quantity"]
        unit_price = Decimal(item_data["unit_price"])
        item = StockOutItem(
            stock_out=stock_out,
            subtotal=quantity * unit_price,
            **item_data,
        )
        item.full_clean()
        item.save()
    stock_out.full_clean()
    return stock_out


@transaction.atomic
def complete_stock_out(*, stock_out, approved_by):
    stock_out = (
        StockOut.objects.select_for_update()
        .prefetch_related("items__product", "items__variant")
        .get(pk=stock_out.pk)
    )
    if stock_out.status == StockOut.Status.COMPLETED:
        return stock_out
    if stock_out.status == StockOut.Status.CANCELLED:
        raise ValidationError("Không thể hoàn tất phiếu đã hủy.")
    if not stock_out.items.exists():
        raise ValidationError("Phiếu xuất phải có ít nhất một sản phẩm.")
    old_status = stock_out.status

    locked_items = []
    for item in stock_out.items.all():
        inventory = get_inventory_for_update(
            stock_out.warehouse,
            item.product,
            item.variant,
        )
        if item.quantity > inventory.quantity_available:
            raise ValidationError("Số lượng xuất vượt quá số lượng tồn kho hiện tại.")
        locked_items.append((item, inventory))

    for item, inventory in locked_items:
        quantity_before = inventory.quantity_on_hand
        inventory.quantity_on_hand -= item.quantity
        inventory.save(update_fields=["quantity_on_hand", "updated_at"])
        transaction_type = (
            InventoryTransaction.TransactionType.TRANSFER_OUT
            if stock_out.reason == StockOut.Reason.TRANSFER
            else InventoryTransaction.TransactionType.STOCK_OUT
        )
        InventoryTransaction.objects.create(
            warehouse=stock_out.warehouse,
            product=item.product,
            variant=item.variant,
            transaction_type=transaction_type,
            quantity=item.quantity,
            quantity_before=quantity_before,
            quantity_after=inventory.quantity_on_hand,
            reference_type="StockOut",
            reference_id=stock_out.id,
            note=f"Hoàn tất phiếu xuất {stock_out.code}",
            created_by=approved_by,
        )

        if stock_out.reason == StockOut.Reason.TRANSFER:
            destination = get_inventory_for_update(
                stock_out.destination_warehouse,
                item.product,
                item.variant,
            )
            destination_before = destination.quantity_on_hand
            destination.quantity_on_hand += item.quantity
            destination.save(update_fields=["quantity_on_hand", "updated_at"])
            InventoryTransaction.objects.create(
                warehouse=stock_out.destination_warehouse,
                product=item.product,
                variant=item.variant,
                transaction_type=(InventoryTransaction.TransactionType.TRANSFER_IN),
                quantity=item.quantity,
                quantity_before=destination_before,
                quantity_after=destination.quantity_on_hand,
                reference_type="StockOut",
                reference_id=stock_out.id,
                note=f"Nhận chuyển kho từ phiếu {stock_out.code}",
                created_by=approved_by,
            )

    stock_out.status = StockOut.Status.COMPLETED
    stock_out.approved_by = approved_by
    stock_out.save(update_fields=["status", "approved_by", "updated_at"])
    record_audit(
        store=stock_out.store,
        user=approved_by,
        action=AuditLog.Action.STOCK_OUT,
        module="stock_out",
        instance=stock_out,
        old_data={"status": old_status},
        new_data={"status": stock_out.status},
    )
    return stock_out
