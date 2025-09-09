# ventas/urls.py
from django.urls import path
from . import views

app_name = "ventas"

urlpatterns = [
    path("registrar/", views.registrar_venta, name="registrar"),
]

