from django.urls import path

from . import views

urlpatterns = [
    path("", views.order_list_view, name="orders"),
    path("race-condition/", views.race_condition_view, name="race_condition"),
]
