from django.urls import path

from . import views

urlpatterns = [path("", views.supplier_list_view, name="suppliers")]
