from django.shortcuts import render

from apps.accounts.rbac import store_permission_required


@store_permission_required("supplier.view")
def supplier_list_view(request):
    return render(request, "suppliers.html")
