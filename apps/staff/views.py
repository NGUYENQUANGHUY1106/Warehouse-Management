from django.shortcuts import render

from apps.accounts.rbac import store_permission_required


@store_permission_required("user.view")
def staff_view(request):
    return render(request, "staff.html")
