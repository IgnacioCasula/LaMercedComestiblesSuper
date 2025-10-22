from django.urls import path
from . import views  # <-- LÍNEA CORREGIDA: Usamos una importación relativa

app_name = 'caja'

urlpatterns = [
    path('menu/', views.menu_caja_view, name='menu_caja'),
    path('apertura/', views.apertura_caja_view, name='apertura_caja'),
]