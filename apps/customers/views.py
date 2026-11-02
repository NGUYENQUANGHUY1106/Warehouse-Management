from django.shortcuts import render

from apps.accounts.rbac import store_permission_required


@store_permission_required("customer.view")
def customer_list_view(request):
    return render(request, "customers.html")
