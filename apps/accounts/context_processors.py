from .rbac import active_memberships, get_active_membership, permission_codes


def rbac_context(request):
    if not request.user.is_authenticated:
        return {}
    memberships = active_memberships(request.user)
    membership = get_active_membership(request)
    store_id = membership.store_id if membership else None
    return {
        "active_membership": membership,
        "available_memberships": memberships,
        "active_store": membership.store if membership else None,
        "rbac_permissions": permission_codes(request.user, store_id),
        "is_store_admin": request.user.is_superuser
        or bool(membership and membership.role.name == "Admin"),
    }
