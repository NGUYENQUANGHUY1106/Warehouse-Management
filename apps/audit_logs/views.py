from django.shortcuts import render

from apps.accounts.rbac import store_permission_required


@store_permission_required("audit.view")
def audit_logs_view(request):
    return render(request, "audit_logs.html")
