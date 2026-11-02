from django.urls import path

from . import views

urlpatterns = [
    path("", views.product_list_view, name="product_list"),
    path("new/", views.product_create_view, name="product_create"),
    path("catalog/", views.catalog_view, name="catalog"),
    path("catalog/category/new/", views.category_create_view, name="category_create"),
    path(
        "catalog/category/<uuid:pk>/edit/",
        views.category_edit_view,
        name="category_edit",
    ),
    path("catalog/brand/new/", views.brand_create_view, name="brand_create"),
    path(
        "catalog/brand/<uuid:pk>/edit/",
        views.brand_edit_view,
        name="brand_edit",
    ),
    path(
        "catalog/<str:entity>/<uuid:pk>/delete/",
        views.catalog_delete_view,
        name="catalog_delete",
    ),
    path("<uuid:pk>/", views.product_detail_view, name="product_detail"),
    path("<uuid:pk>/edit/", views.product_edit_view, name="product_edit"),
    path("<uuid:pk>/delete/", views.product_delete_view, name="product_delete"),
    path("<uuid:pk>/restore/", views.product_restore_view, name="product_restore"),
    path(
        "<uuid:pk>/images/add/", views.product_image_add_view, name="product_image_add"
    ),
    path(
        "<uuid:pk>/images/<uuid:image_id>/delete/",
        views.product_image_delete_view,
        name="product_image_delete",
    ),
    path(
        "<uuid:pk>/variants/add/",
        views.product_variant_add_view,
        name="product_variant_add",
    ),
    path(
        "<uuid:pk>/variants/<uuid:variant_id>/delete/",
        views.product_variant_delete_view,
        name="product_variant_delete",
    ),
]
