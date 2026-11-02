from django.shortcuts import render

from apps.accounts.rbac import store_permission_required


@store_permission_required("report.view")
def reports_view(request):
    return render(request, "reports.html")
