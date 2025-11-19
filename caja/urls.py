from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    path('menu/', views.menu_caja_view, name='menu_caja'),
    path('apertura/', views.apertura_caja_view, name='apertura_caja'),
    path('cierre/', views.cierre_caja_view, name='cierre_caja'),
    path('ultimo-cierre/', views.obtener_ultimo_cierre, name='ultimo_cierre'),
    
    
    path('movimientos-caja/menu/', views.movimientos_caja_menu_view, name='movimientos_caja_menu'),
    path('movimientos-caja/agregar/', views.agregar_movimiento_caja_view, name='agregar_movimiento_caja'),
    path('movimientos-caja/ver/', views.ver_movimientos_caja_view, name='ver_movimientos_caja'),
    path('movimientos-caja/api/', views.api_movimientos_caja, name='api_movimientos_caja'),
    path('movimientos-caja/api/filtros-dependientes/', views.api_filtros_dependientes, name='api_filtros_dependientes'), 
]