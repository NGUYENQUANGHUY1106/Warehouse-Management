from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("store/", views.store_management_view, name="store_management"),
]
