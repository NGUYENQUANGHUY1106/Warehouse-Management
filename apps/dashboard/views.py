from django.shortcuts import render

from apps.accounts.rbac import store_permission_required


@store_permission_required()
def dashboard_view(request):
    return render(request, "dashboard.html")


@store_permission_required("store.view")
def store_management_view(request):
    return render(request, "store_management.html")
