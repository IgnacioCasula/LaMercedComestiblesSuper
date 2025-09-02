from django.urls import path

from caja import views

urlpatterns = [
    path("menu/", views.menu_caja_view, name="menu_caja"),
    path("apertura/", views.apertura_caja_view, name="apertura_caja"),
]