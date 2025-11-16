from django.urls import path
from . import views

app_name = 'asistencias'

urlpatterns = [
    path('', views.ver_asistencias, name='ver_asistencias'),
    path('calendar-events/', views.calendar_events, name='calendar_events'),
]