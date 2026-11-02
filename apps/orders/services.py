from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit_logs.models import AuditLog
from apps.audit_logs.services import record_audit
from apps.inventory.models import InventoryReservation
from apps.inventory.services import (
    consume_inventory,
    release_inventory,
    reserve_inventory,
)

from .models import Order, OrderItem, OrderStatusHistory


def _record_status(order, old_status, new_status, user, note=""):
    OrderStatusHistory.objects.create(
        order=order,
        old_status=old_status,
        new_status=new_status,
        changed_by=user,
        note=note,
    )
    record_audit(
        store=order.store,
        user=user,
        action=AuditLog.Action.ORDER_STATUS_CHANGE,
        module="orders",
        instance=order,
        old_data={"status": old_status},
        new_data={"status": new_status},
    )


@transaction.atomic
def create_order(*, data, items, created_by, reserve=True):
    order = Order(
        created_by=created_by,
        order_date=data.pop("order_date", timezone.now()),
        **data,
    )
    order.full_clean()
    order.save()
    subtotal = Decimal("0")
    for item_data in items:
        quantity = item_data["quantity"]
        unit_price = Decimal(item_data["unit_price"])
        discount = Decimal(item_data.get("discount", 0))
        line_subtotal = quantity * unit_price - discount
        item = OrderItem(
            order=order,
            subtotal=line_subtotal,
            **item_data,
        )
        item.full_clean()
        item.save()
        subtotal += line_subtotal
        if reserve:
            reserve_inventory(
                order=order,
                product=item.product,
                variant=item.variant,
                quantity=item.quantity,
                user=created_by,
            )

    order.subtotal = subtotal
    order.total = subtotal - order.discount + order.shipping_fee + order.tax
    order.full_clean()
    order.save(update_fields=["subtotal", "total", "updated_at"])
    _record_status(order, "", order.status, created_by, "Tạo đơn hàng")
    return order


@transaction.atomic
def confirm_order(*, order, user):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != Order.Status.PENDING:
        raise ValidationError("Chỉ đơn chờ xác nhận mới có thể xác nhận.")
    old_status = order.status
    if not order.reservations.filter(
        status=InventoryReservation.Status.ACTIVE
    ).exists():
        for item in order.items.select_related("product", "variant"):
            reserve_inventory(
                order=order,
                product=item.product,
                variant=item.variant,
                quantity=item.quantity,
                user=user,
            )
    order.status = Order.Status.CONFIRMED
    order.save(update_fields=["status", "updated_at"])
    _record_status(order, old_status, order.status, user)
    return order


@transaction.atomic
def complete_order(*, order, user):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status in {Order.Status.COMPLETED, Order.Status.CANCELLED}:
        raise ValidationError("Trạng thái đơn hàng không hợp lệ.")
    reservations = list(
        order.reservations.select_for_update().filter(
            status=InventoryReservation.Status.ACTIVE
        )
    )
    if not reservations:
        raise ValidationError("Đơn hàng không có phiên giữ hàng hợp lệ.")
    old_status = order.status
    for reservation in reservations:
        consume_inventory(reservation=reservation, user=user)
    order.status = Order.Status.COMPLETED
    order.payment_status = Order.PaymentStatus.PAID
    order.save(update_fields=["status", "payment_status", "updated_at"])
    _record_status(order, old_status, order.status, user)
    return order


@transaction.atomic
def cancel_order(*, order, user, note=""):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status == Order.Status.COMPLETED:
        raise ValidationError("Không thể hủy đơn đã hoàn thành.")
    if order.status == Order.Status.CANCELLED:
        return order
    old_status = order.status
    reservations = list(
        order.reservations.select_for_update().filter(
            status=InventoryReservation.Status.ACTIVE
        )
    )
    for reservation in reservations:
        release_inventory(reservation=reservation, user=user)
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])
    _record_status(order, old_status, order.status, user, note)
    return order
