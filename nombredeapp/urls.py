from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('seleccionar-rol/', views.seleccionar_rol_view, name='seleccionar_rol'),
    path('inicio/', views.inicio_view, name='inicio'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.login_view, name='root_login'),
    path('solicitar-usuario/', views.solicitar_usuario_view, name='solicitar_usuario'),
    path('ingresar-codigo/', views.ingresar_codigo_view, name='ingresar_codigo'),
    path('reenviar-codigo/', views.reenviar_codigo_view, name='reenviar_codigo'),
    path('verificar-email/<uuid:token>/', views.verificar_email_view, name='verificar_email'),
    path('cambiar-contrasena/', views.cambiar_contrasena_view, name='cambiar_contrasena'),
    path('acceso-denegado/', views.acceso_denegado_view, name='acceso_denegado'),
]
