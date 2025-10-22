from django.urls import path
from . import views

urlpatterns = [
    path('', views.gestion_de_stock, name='gestion_de_stock'),
]
