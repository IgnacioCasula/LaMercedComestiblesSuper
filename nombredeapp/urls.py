from django.urls import path
from . import views

urlpatterns = [
    path('', views.iniciar_sesion, name='iniciar_sesion'),
    path('seleccionar-rol/', views.seleccionar_rol, name='seleccionar_rol'),
    path('inicio/', views.pagina_inicio, name='inicio'),
    path('cerrar-sesion/', views.cerrar_sesion, name='cerrar_sesion'),
    path('recuperar/solicitar-usuario/', views.solicitar_usuario, name='solicitar_usuario'),
    path('recuperar/ingresar-codigo/', views.ingresar_codigo, name='ingresar_codigo'),
    path('recuperar/reenviar-codigo/', views.reenviar_codigo, name='reenviar_codigo'),
    path('recuperar/verificar-email/<uuid:token>/', views.verificar_email, name='verificar_email'),
    path('recuperar/cambiar-contrasena/', views.cambiar_contrasena, name='cambiar_contrasena'),
    path('recuperar/acceso-denegado/', views.acceso_denegado, name='acceso_denegado'),
    path('empleados/crear/', views.crear_empleado_vista, name='crear_empleado'),
    path('api/areas/', views.api_areas, name='api_areas'),
    path('api/areas/crear/', views.api_crear_area, name='api_crear_area'),
    path('api/puestos/<int:area_id>/', views.api_puestos_por_area, name='api_puestos_por_area'),
    path('api/puestos/crear/', views.api_crear_puesto, name='api_crear_puesto'),
    path('api/empleados/registrar/', views.api_registrar_empleado, name='api_registrar_empleado'),
]