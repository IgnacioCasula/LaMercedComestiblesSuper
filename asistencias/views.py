from django.shortcuts import render, redirect
from nombredeapp.decorators import permiso_requerido
from caja.models import Empleados, Asistencias, Roles, Area
from .models import Horario
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
from collections import defaultdict

@permiso_requerido('asistencias:ver_asistencias')
def ver_asistencias(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('iniciar_sesion')
    
    try:
        empleado = Empleados.objects.select_related('idusuarios').get(idusuarios_id=usuario_id)
    except Empleados.DoesNotExist:
        return redirect('inicio')

    context = {
        'empleado': empleado,
    }
    return render(request, 'asistencias/asistencias.html', context)

def calendar_events(request):
    usuario_id = request.session.get('usuario_id')
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    if not all([usuario_id, start_str, end_str]):
        return JsonResponse([], safe=False)

    empleado = Empleados.objects.get(idusuarios_id=usuario_id)
    start_date = datetime.fromisoformat(start_str.split('T')[0]).date()
    end_date = datetime.fromisoformat(end_str.split('T')[0]).date()

    horarios = Horario.objects.filter(empleado=empleado).prefetch_related('dias__tramos', 'rol__area')
    asistencias = Asistencias.objects.filter(
        idempleado=empleado, 
        fechaasistencia__range=[start_date, end_date]
    ).select_related('rol')

    events = []
    
    asistencias_map = defaultdict(list)
    for a in asistencias:
        asistencias_map[a.fechaasistencia].append(a)

    current_date = start_date
    while current_date < end_date:
        dia_semana_actual = current_date.weekday()
        
        turnos_programados = []
        for horario in horarios:
            for dia in horario.dias.filter(dia_semana=dia_semana_actual):
                for tramo in dia.tramos.all():
                    turnos_programados.append({'horario': horario, 'tramo': tramo})
        
        asistencias_del_dia = asistencias_map.get(current_date, [])
        asistencias_procesadas = set()

        for turno in turnos_programados:
            horario = turno['horario']
            tramo = turno['tramo']
            rol = horario.rol
            
            fecha_hora_inicio = datetime.combine(current_date, tramo.hora_inicio)
            fecha_hora_fin = datetime.combine(current_date, tramo.hora_fin)
            if tramo.hora_fin < tramo.hora_inicio:
                fecha_hora_fin += timedelta(days=1)
            
            mejor_asistencia = None
            min_diff = float('inf')

            for asistencia in asistencias_del_dia:
                if asistencia.rol == rol and asistencia.id not in asistencias_procesadas:
                    hora_entrada_reg = datetime.combine(current_date, asistencia.horaentrada)
                    diff = abs((hora_entrada_reg - fecha_hora_inicio).total_seconds())
                    if diff < min_diff:
                        min_diff = diff
                        mejor_asistencia = asistencia

            titulo = f"{rol.nombrerol if rol else 'Sin Rol'}"
            area = rol.area.nombrearea if rol and rol.area else 'Sin Área'

            if mejor_asistencia:
                asistencias_procesadas.add(mejor_asistencia.id)
                hora_entrada_reg = datetime.combine(current_date, mejor_asistencia.horaentrada)
                diff_puntualidad = (hora_entrada_reg - fecha_hora_inicio).total_seconds()
                
                estado, color = ("Justo", "#27ae60")
                if diff_puntualidad < -900: estado, color = ("Temprano", "#3498db")
                elif diff_puntualidad > 300: estado, color = ("Tarde", "#e67e22")

                events.append({
                    'title': titulo, 'start': fecha_hora_inicio.isoformat(), 'end': fecha_hora_fin.isoformat(), 'color': color,
                    'extendedProps': {'area': area, 'estado': estado, 'entrada_registrada': mejor_asistencia.horaentrada.strftime('%H:%M')}
                })
            else: 
                if current_date < timezone.now().date(): 
                    estado, color = ('Ausente', '#e74c3c')
                else: 
                    estado, color = ('Programado', '#95a5a6') # Gris más oscuro para mejor visibilidad
                
                events.append({
                    'title': titulo, 'start': fecha_hora_inicio.isoformat(), 'end': fecha_hora_fin.isoformat(), 'color': color,
                    'extendedProps': {'area': area, 'estado': estado, 'entrada_registrada': 'N/A'}
                })

        for asistencia in asistencias_del_dia:
            if asistencia.id not in asistencias_procesadas:
                titulo = f"{asistencia.rol.nombrerol if asistencia.rol else 'Sin Rol'}"
                area = asistencia.rol.area.nombrearea if asistencia.rol and asistencia.rol.area else 'Sin Área'
                events.append({
                    'title': titulo,
                    'start': datetime.combine(current_date, asistencia.horaentrada).isoformat(),
                    'color': '#8e44ad',
                    'extendedProps': {'area': area, 'estado': 'Fuera de Turno', 'entrada_registrada': asistencia.horaentrada.strftime('%H:%M')}
                })

        current_date += timedelta(days=1)
        
    return JsonResponse(events, safe=False)