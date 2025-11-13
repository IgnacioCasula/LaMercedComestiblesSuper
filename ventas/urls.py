from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('registrar/', views.registrar_venta, name='registrar_venta'),
    path('buscar-productos/', views.buscar_productos, name='buscar_productos'),
    path('procesar-venta/', views.procesar_venta, name='procesar_venta'),
    path('venta/<int:venta_id>/', views.obtener_detalle_venta, name='detalle_venta'),
]