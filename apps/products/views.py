from django.shortcuts import render

from apps.accounts.rbac import store_permission_required


@store_permission_required("product.view")
def product_list_view(request):
    return render(request, "products.html")
