from django.shortcuts import render, redirect
from nombredeapp.decorators import permiso_requerido
from caja.models import Empleados, Asistencias, Roles, Area
from .models import Horario
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
from collections import defaultdict
import math

def get_week_of_month(date):
    """
    Calcula el número de semana dentro de un mes (1-4).
    Una semana se considera iniciada el lunes.
    """
    first_day_of_month = date.replace(day=1)
    first_day_weekday = first_day_of_month.weekday()
    adjusted_day = date.day + first_day_weekday
    week_number = math.ceil(adjusted_day / 7)
    return min(week_number, 4)

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
        fechaasistencia__gte=start_date,
        fechaasistencia__lt=end_date
    ).select_related('rol')

    events = []
    
    asistencias_map = defaultdict(list)
    for a in asistencias:
        asistencias_map[a.fechaasistencia].append(a)
    horarios_por_semana = defaultdict(list)
    for horario in horarios:
        for dia in horario.dias.all():
            horarios_por_semana[dia.semana_del_mes].append({'horario': horario, 'dia': dia})
    
    num_semanas_configuradas = len(horarios_por_semana)

    total_days = (end_date - start_date).days
    for day_offset in range(total_days):
        current_date = start_date + timedelta(days=day_offset)
        dia_semana_actual = current_date.weekday()
        semana_del_mes_actual = get_week_of_month(current_date)
        semana_a_usar = 1
        if num_semanas_configuradas == 1:
            semana_a_usar = 1
        elif num_semanas_configuradas == 2:
            semana_a_usar = 1 if semana_del_mes_actual in [1, 3] else 2
        elif num_semanas_configuradas == 4:
            semana_a_usar = semana_del_mes_actual
        elif num_semanas_configuradas == 3:
            month_cycle = (current_date.month - 1) % 3
            if month_cycle == 0:
                mapping = {1: 1, 2: 2, 3: 3, 4: 1}
            elif month_cycle == 1:
                mapping = {1: 2, 2: 3, 3: 1, 4: 2}
            else:
                mapping = {1: 3, 2: 1, 3: 2, 4: 3}
            semana_a_usar = mapping[semana_del_mes_actual]

        turnos_programados = []
        dias_horario_aplicables = horarios_por_semana.get(semana_a_usar, [])
        for item in dias_horario_aplicables:
            if item['dia'].dia_semana == dia_semana_actual:
                for tramo in item['dia'].tramos.all():
                    turnos_programados.append({'horario': item['horario'], 'tramo': tramo})
        
        asistencias_del_dia = asistencias_map.get(current_date, [])
        asistencias_procesadas = set()

        for turno in turnos_programados:
            horario = turno['horario']
            tramo = turno['tramo']
            rol = horario.rol

            if not tramo.hora_inicio or not tramo.hora_fin:
                continue
            
            fecha_hora_inicio = timezone.make_aware(datetime.combine(current_date, tramo.hora_inicio))
            fecha_hora_fin = timezone.make_aware(datetime.combine(current_date, tramo.hora_fin))
            if tramo.hora_fin < tramo.hora_inicio:
                fecha_hora_fin += timedelta(days=1)
            
            mejor_asistencia = None
            min_diff = float('inf')
            margen_busqueda_inicio = fecha_hora_inicio - timedelta(minutes=30)

            for asistencia in asistencias_del_dia:
                if asistencia.rol == rol and asistencia.idasistencia not in asistencias_procesadas and asistencia.horaentrada:
                    hora_entrada_reg = timezone.make_aware(datetime.combine(current_date, asistencia.horaentrada))
                    if hora_entrada_reg >= margen_busqueda_inicio:
                        diff = abs((hora_entrada_reg - fecha_hora_inicio).total_seconds())
                        if diff < min_diff:
                            min_diff = diff
                            mejor_asistencia = asistencia

            titulo = f"{rol.nombrerol if rol else 'Sin Rol'}"
            area = rol.area.nombrearea if rol and rol.area else 'Sin Área'

            if mejor_asistencia:
                asistencias_procesadas.add(mejor_asistencia.idasistencia)
                hora_entrada_reg = timezone.make_aware(datetime.combine(current_date, mejor_asistencia.horaentrada))
                diff_puntualidad = (hora_entrada_reg - fecha_hora_inicio).total_seconds()
                if diff_puntualidad <= -600:
                    estado, className = ("Temprano", "event-temprano")
                elif diff_puntualidad > 300:
                    estado, className = ("Tarde", "event-tarde")
                else:
                    estado, className = ("Justo", "event-justo")

                events.append({
                    'title': titulo, 'start': fecha_hora_inicio.isoformat(), 'end': fecha_hora_fin.isoformat(), 
                    'classNames': [className],
                    'extendedProps': {'area': area, 'estado': estado, 'entrada_registrada': mejor_asistencia.horaentrada.strftime('%H:%M')}
                })
            else: 
                event_data = {
                    'title': titulo, 'start': fecha_hora_inicio.isoformat(), 'end': fecha_hora_fin.isoformat(),
                    'extendedProps': {'area': area, 'entrada_registrada': 'N/A'}
                }
                if current_date < timezone.localdate(): 
                    event_data['extendedProps']['estado'] = 'Ausente'
                    event_data['classNames'] = ['event-ausente']
                else: 
                    event_data['extendedProps']['estado'] = 'Programado'
                    event_data['classNames'] = ['event-programado']
                
                events.append(event_data)

        for asistencia in asistencias_del_dia:
            if asistencia.idasistencia not in asistencias_procesadas:
                titulo = f"{asistencia.rol.nombrerol if asistencia.rol else 'Sin Rol'}"
                area = asistencia.rol.area.nombrearea if asistencia.rol and asistencia.rol.area else 'Sin Área'
                start_time = timezone.make_aware(datetime.combine(current_date, asistencia.horaentrada)) if asistencia.horaentrada else None
                events.append({
                    'title': titulo,
                    'start': start_time.isoformat() if start_time else None,
                    'classNames': ['event-fuera-de-turno'],
                    'extendedProps': {'area': area, 'estado': 'Fuera de Turno', 'entrada_registrada': asistencia.horaentrada.strftime('%H:%M') if asistencia.horaentrada else 'N/A'}
                })
        
    return JsonResponse(events, safe=False)