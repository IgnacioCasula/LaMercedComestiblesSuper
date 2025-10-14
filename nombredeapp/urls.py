from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('enviar-codigo/', views.enviar_codigo_view, name='enviar_codigo'),
    path('reenviar-codigo/', views.reenviar_codigo_view, name='reenviar_codigo'),
    path('ingresar-codigo/', views.ingresar_codigo_view, name='ingresar_codigo'),
    path('cambiar-contrasena/', views.cambiar_contrasena_view, name='cambiar_contrasena'),
    path('seleccionar-rol/', views.seleccionar_rol_view, name='seleccionar_rol'),
    path('inicio/', views.inicio_view, name='inicio'),
    path('logout/', views.logout_view, name='logout'),
    path('crear-empleado/', views.crear_empleado_view, name='crear_empleado'),
    path('lista-empleados/', views.lista_empleados_view, name='lista_empleados'),
    path('gestion-stock/', views.gestion_stock_view, name='gestion_stock'),
    
    # Rutas de API para crear empleado
    path('api/areas/', views.api_areas, name='api_areas'),
    path('api/areas/crear/', views.api_crear_area, name='api_crear_area'),
    path('api/puestos/<str:area_id>/', views.api_puestos_por_area, name='api_puestos_por_area'),
    path('api/puestos/crear/', views.api_crear_puesto, name='api_crear_puesto'),
    path('api/registrar-empleado/', views.api_registrar_empleado, name='api_registrar_empleado'),
]