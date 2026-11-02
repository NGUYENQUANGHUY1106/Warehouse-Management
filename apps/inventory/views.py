from django.shortcuts import render

from apps.accounts.rbac import store_permission_required


@store_permission_required("stockin.view")
def stock_in_view(request):
    return render(request, "stock_in.html")


@store_permission_required("stockout.view")
def stock_out_view(request):
    return render(request, "stock_out.html")


@store_permission_required("inventory.view")
def inventory_view(request):
    return render(request, "inventory.html")
