
from django.urls import path

from caja import views

urlpatterns = [
    path('', views.hola, name='caja'),
    
    ]