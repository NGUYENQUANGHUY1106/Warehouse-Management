from .models import AuditLog


def record_audit(
    *,
    store,
    user,
    action,
    module,
    instance,
    old_data=None,
    new_data=None,
    ip_address=None,
    user_agent="",
):
    """Append an immutable audit event inside the caller's transaction."""
    return AuditLog.objects.create(
        store=store,
        user=user,
        action=action,
        module=module,
        object_type=instance._meta.label,
        object_id=instance.pk,
        object_repr=str(instance),
        old_data=old_data or {},
        new_data=new_data or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
