from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    path('menu/', views.menu_caja_view, name='menu_caja'),
    path('apertura/', views.apertura_caja_view, name='apertura_caja'),
    path('cierre/', views.cierre_caja_view, name='cierre_caja'),
]