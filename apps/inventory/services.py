from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.audit_logs.models import AuditLog
from apps.audit_logs.services import record_audit

from .models import Inventory, InventoryReservation, InventoryTransaction


def get_inventory_for_update(warehouse, product, variant=None):
    lookup = {
        "warehouse": warehouse,
        "product": product,
        "variant": variant,
    }
    inventory = (
        Inventory.objects.select_for_update(of=("self",))
        .filter(**lookup)
        .order_by()
        .first()
    )
    if inventory:
        return inventory

    try:
        with transaction.atomic():
            Inventory.objects.create(
                **lookup,
                min_stock_level=product.min_stock_level,
            )
    except IntegrityError:
        pass

    return Inventory.objects.select_for_update(of=("self",)).order_by().get(**lookup)


@transaction.atomic
def reserve_inventory(
    *,
    order,
    product,
    quantity,
    variant=None,
    hold_minutes=5,
    user=None,
):
    if quantity <= 0:
        raise ValidationError("Số lượng giữ phải lớn hơn 0.")
    if product.store_id != order.store_id:
        raise ValidationError("Sản phẩm không thuộc gian hàng của đơn hàng.")
    if variant and variant.product_id != product.id:
        raise ValidationError("Biến thể không thuộc sản phẩm.")

    inventory = get_inventory_for_update(order.warehouse, product, variant)
    available = inventory.quantity_available
    if quantity > available:
        raise ValidationError("Số lượng giữ vượt quá số lượng tồn kho hiện tại.")

    existing = InventoryReservation.objects.select_for_update().filter(
        order=order,
        warehouse=order.warehouse,
        product=product,
        variant=variant,
        status=InventoryReservation.Status.ACTIVE,
    )
    if existing.exists():
        raise ValidationError("Sản phẩm đã được giữ cho đơn hàng này.")

    reservation = InventoryReservation.objects.create(
        order=order,
        warehouse=order.warehouse,
        product=product,
        variant=variant,
        quantity=quantity,
        expires_at=timezone.now() + timedelta(minutes=hold_minutes),
    )
    inventory.quantity_reserved += quantity
    inventory.save(update_fields=["quantity_reserved", "updated_at"])

    InventoryTransaction.objects.create(
        warehouse=inventory.warehouse,
        product=product,
        variant=variant,
        transaction_type=InventoryTransaction.TransactionType.RESERVE,
        quantity=quantity,
        quantity_before=inventory.quantity_on_hand,
        quantity_after=inventory.quantity_on_hand,
        reference_type="InventoryReservation",
        reference_id=reservation.id,
        note=f"Giữ hàng cho đơn {order.code}",
        created_by=user or order.created_by,
    )
    return reservation


@transaction.atomic
def release_inventory(*, reservation, expired=False, user=None):
    reservation = InventoryReservation.objects.select_for_update().get(
        pk=reservation.pk
    )
    if reservation.status != InventoryReservation.Status.ACTIVE:
        return reservation

    inventory = get_inventory_for_update(
        reservation.warehouse,
        reservation.product,
        reservation.variant,
    )
    if inventory.quantity_reserved < reservation.quantity:
        raise ValidationError("Dữ liệu tồn giữ không nhất quán.")

    inventory.quantity_reserved -= reservation.quantity
    inventory.save(update_fields=["quantity_reserved", "updated_at"])
    reservation.status = (
        InventoryReservation.Status.EXPIRED
        if expired
        else InventoryReservation.Status.RELEASED
    )
    reservation.save(update_fields=["status", "updated_at"])

    InventoryTransaction.objects.create(
        warehouse=inventory.warehouse,
        product=reservation.product,
        variant=reservation.variant,
        transaction_type=InventoryTransaction.TransactionType.RELEASE,
        quantity=reservation.quantity,
        quantity_before=inventory.quantity_on_hand,
        quantity_after=inventory.quantity_on_hand,
        reference_type="InventoryReservation",
        reference_id=reservation.id,
        note=(
            "Hết thời gian giữ hàng"
            if expired
            else f"Nhả hàng giữ của đơn {reservation.order.code}"
        ),
        created_by=user,
    )
    return reservation


@transaction.atomic
def consume_inventory(*, reservation, user=None):
    reservation = InventoryReservation.objects.select_for_update().get(
        pk=reservation.pk
    )
    if reservation.status != InventoryReservation.Status.ACTIVE:
        raise ValidationError("Phiên giữ hàng không còn hiệu lực.")
    if reservation.expires_at <= timezone.now():
        raise ValidationError("Phiên giữ hàng đã hết hạn.")

    inventory = get_inventory_for_update(
        reservation.warehouse,
        reservation.product,
        reservation.variant,
    )
    if (
        inventory.quantity_reserved < reservation.quantity
        or inventory.quantity_on_hand < reservation.quantity
    ):
        raise ValidationError("Tồn kho không đủ để hoàn tất đơn hàng.")

    quantity_before = inventory.quantity_on_hand
    inventory.quantity_on_hand -= reservation.quantity
    inventory.quantity_reserved -= reservation.quantity
    inventory.save(
        update_fields=["quantity_on_hand", "quantity_reserved", "updated_at"]
    )
    reservation.status = InventoryReservation.Status.CONSUMED
    reservation.save(update_fields=["status", "updated_at"])

    InventoryTransaction.objects.create(
        warehouse=inventory.warehouse,
        product=reservation.product,
        variant=reservation.variant,
        transaction_type=InventoryTransaction.TransactionType.SALE,
        quantity=reservation.quantity,
        quantity_before=quantity_before,
        quantity_after=inventory.quantity_on_hand,
        reference_type="Order",
        reference_id=reservation.order_id,
        note=f"Hoàn tất đơn {reservation.order.code}",
        created_by=user or reservation.order.created_by,
    )
    return reservation


@transaction.atomic
def release_expired_reservations(*, now=None):
    now = now or timezone.now()
    reservations = list(
        InventoryReservation.objects.select_for_update(of=("self",))
        .filter(
            status=InventoryReservation.Status.ACTIVE,
            expires_at__lte=now,
        )
        .select_related("warehouse", "product", "variant", "order")
    )
    for reservation in reservations:
        release_inventory(reservation=reservation, expired=True)
    return len(reservations)


@transaction.atomic
def adjust_inventory(
    *,
    warehouse,
    product,
    quantity_after,
    variant=None,
    note="",
    user=None,
):
    if quantity_after < 0:
        raise ValidationError("Tồn kho không được âm.")
    inventory = get_inventory_for_update(warehouse, product, variant)
    if quantity_after < inventory.quantity_reserved:
        raise ValidationError("Tồn mới không được thấp hơn số lượng đang giữ.")
    quantity_before = inventory.quantity_on_hand
    difference = abs(quantity_after - quantity_before)
    if difference == 0:
        return inventory
    inventory.quantity_on_hand = quantity_after
    inventory.save(update_fields=["quantity_on_hand", "updated_at"])
    InventoryTransaction.objects.create(
        warehouse=warehouse,
        product=product,
        variant=variant,
        transaction_type=InventoryTransaction.TransactionType.ADJUSTMENT,
        quantity=difference,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        note=note,
        created_by=user,
    )
    record_audit(
        store=warehouse.store,
        user=user,
        action=AuditLog.Action.INVENTORY_ADJUSTMENT,
        module="inventory",
        instance=inventory,
        old_data={"quantity_on_hand": quantity_before},
        new_data={"quantity_on_hand": quantity_after},
    )
    return inventory
