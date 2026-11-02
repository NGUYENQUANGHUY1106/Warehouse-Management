from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("inventory_project.api_urls")),
    path("", lambda request: redirect("login")),
    path("login/", include("apps.accounts.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("products/", include("apps.products.urls")),
    path("inventory/", include("apps.inventory.urls")),
    path("orders/", include("apps.orders.urls")),
    path("customers/", include("apps.customers.urls")),
    path("suppliers/", include("apps.suppliers.urls")),
    path("staff/", include("apps.staff.urls")),
    path("reports/", include("apps.reports.urls")),
    path("settings/", include("apps.settings_app.urls")),
    path("audit-logs/", include("apps.audit_logs.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
