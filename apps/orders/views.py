from django.shortcuts import render

from apps.accounts.rbac import store_permission_required


@store_permission_required("order.view")
def order_list_view(request):
    return render(request, "orders.html")


@store_permission_required("order.view")
def race_condition_view(request):
    return render(request, "race_condition.html")
