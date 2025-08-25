from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('seleccionar-rol/', views.seleccionar_rol_view, name='seleccionar_rol'),
    path('inicio/', views.inicio_view, name='inicio'),
    path('logout/', views.logout_view, name='logout'),
    # Redirigir la raíz del sitio a la página de login
    path('', views.login_view, name='root_login'),
]