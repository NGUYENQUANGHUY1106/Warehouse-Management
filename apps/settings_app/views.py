from django.shortcuts import render

from apps.accounts.rbac import store_permission_required


@store_permission_required("store.manage")
def settings_view(request):
    return render(request, "settings.html")
