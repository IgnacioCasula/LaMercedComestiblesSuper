from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('registrar/', views.registrar_venta, name='registrar_venta'),
    path('buscar-producto/', views.buscar_producto, name='buscar_producto'),
    path('procesar-venta/', views.procesar_venta, name='procesar_venta'),
    # ✅ NUEVA URL PARA ACTUALIZAR STOCK
    path('obtener-stock-actualizado/', views.obtener_stock_actualizado, name='obtener_stock_actualizado'),
]