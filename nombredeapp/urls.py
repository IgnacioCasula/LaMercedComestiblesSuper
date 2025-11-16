from django.urls import path
from . import views

urlpatterns = [
    # Rutas de autenticación
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('enviar-codigo/', views.enviar_codigo_view, name='enviar_codigo'),
    path('reenviar-codigo/', views.reenviar_codigo_view, name='reenviar_codigo'),
    path('ingresar-codigo/', views.ingresar_codigo_view, name='ingresar_codigo'),
    path('cambiar-contrasena/', views.cambiar_contrasena_view, name='cambiar_contrasena'),
    path('seleccionar-rol/', views.seleccionar_rol_view, name='seleccionar_rol'),
    path('logout/', views.logout_view, name='logout'),
    
    # Rutas principales
    path('inicio/', views.inicio_view, name='inicio'),
    
    # Rutas de gestión de empleados
    path('crear-empleado/', views.crear_empleado_view, name='crear_empleado'),
    path('lista-empleados/', views.lista_empleados_view, name='lista_empleados'),
    
    # Rutas de gestión de áreas y puestos
    path('gestion-areas-puestos/', views.gestion_areas_puestos_view, name='gestion_areas_puestos'),
    
    # Rutas para Caja y Stock
    path('menu-caja/', views.menu_caja_view, name='menu_caja'),
    path('gestion-stock/', views.gestion_stock_view, name='gestion_stock'),
    
    # API Estado de Caja
    path('api/caja-status/', views.api_caja_status, name='api_caja_status'),
    
    # APIs de áreas y puestos
    path('api/areas-puestos/', views.api_areas_puestos, name='api_areas_puestos'),
    path('api/areas-puestos/crear-area/', views.api_crear_area, name='api_crear_area_nueva'),
    path('api/areas-puestos/editar-area/<str:area_nombre>/', views.api_editar_area, name='api_editar_area'),
    path('api/areas-puestos/crear-puesto/', views.api_crear_puesto_nuevo, name='api_crear_puesto_nuevo'),
    path('api/areas-puestos/editar-puesto/<int:puesto_id>/', views.api_editar_puesto, name='api_editar_puesto'),
    
    # APIs para crear empleado
    path('api/areas/', views.api_areas, name='api_areas'),
    path('api/puestos/<str:area_id>/', views.api_puestos_por_area_con_permisos, name='api_puestos_por_area'),
    path('api/registrar-empleado/', views.api_registrar_empleado_actualizado, name='api_registrar_empleado'),
    
    # APIs para lista de empleados
    path('api/empleados/lista/', views.api_lista_empleados, name='api_lista_empleados'),
    path('api/empleados/<int:empleado_id>/', views.api_detalle_empleado, name='api_detalle_empleado'),
    path('api/empleados/<int:empleado_id>/editar/', views.api_editar_empleado, name='api_editar_empleado'),
    
    # APIs simples para selects
    path('api/areas-simple/', views.api_areas_simple, name='api_areas_simple'),
    path('api/puestos-simple/<str:area_nombre>/', views.api_puestos_por_area_simple, name='api_puestos_por_area_simple'),
    
    # APIs de asistencia (manuales - backup)
    path('api/registrar-entrada/', views.registrar_entrada, name='api_registrar_entrada'),
    path('api/registrar-salida/', views.registrar_salida, name='api_registrar_salida'),
    path('api/estado-asistencia-hoy/', views.estado_asistencia_hoy, name='api_estado_asistencia_hoy'),

    path('logs-actividad/', views.logs_actividad_view, name='logs_actividad'),
    path('api/logs-actividad/', views.api_logs_actividad, name='api_logs_actividad'),
    path('api/logs-actividad/<str:log_timestamp>/', views.api_detalle_log, name='api_detalle_log'),

    # APIs para asignar roles adicionales a empleados existentes
    path('api/buscar-empleados/', views.api_buscar_empleados, name='api_buscar_empleados'),
    path('api/empleados/<int:empleado_id>/roles/', views.api_roles_empleado, name='api_roles_empleado'),
    path('api/asignar-nuevo-rol/', views.api_asignar_nuevo_rol, name='api_asignar_nuevo_rol'),
]