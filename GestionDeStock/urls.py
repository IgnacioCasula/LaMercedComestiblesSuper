from django.urls import path
from . import views

urlpatterns = [
    path('', views.gestion, name="gestion"),
    path('productos/', views.productos, name="productos"),
    path('categorias/', views.categorias, name="categorias"),
    path('movimientos/', views.movimientos, name="movimientos"),
    path('reportes/', views.reportes, name="reportes"),
    path('productos/agregar/', views.agregar_producto, name="agregar_producto"),  # ✅ nueva ruta
]
