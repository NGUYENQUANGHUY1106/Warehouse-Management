from django.urls import path

from . import views

urlpatterns = [path("", views.customer_list_view, name="customers")]
