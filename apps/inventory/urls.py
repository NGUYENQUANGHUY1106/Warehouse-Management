from django.urls import path

from . import views

urlpatterns = [
    path("stock-in/", views.stock_in_view, name="stock_in"),
    path("stock-out/", views.stock_out_view, name="stock_out"),
    path("", views.inventory_view, name="inventory"),
]
