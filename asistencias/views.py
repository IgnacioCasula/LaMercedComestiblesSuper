from django.shortcuts import render, redirect
from caja.models import Empleados, Asistencias, Roles, Horario
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
from collections import defaultdict
import math

def get_week_of_month(date):
    """Calcula la semana del mes (1-4)"""
    first_day_of_month = date.replace(day=1)
    first_day_weekday = first_day_of_month.weekday()
    adjusted_day = date.day + first_day_weekday
    week_number = math.ceil(adjusted_day / 7)
    return min(week_number, 4)


def ver_asistencias(request):
    """Vista principal del calendario de asistencias"""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')
    
    try:
        empleado = Empleados.objects.select_related('idusuarios').get(idusuarios_id=usuario_id)
    except Empleados.DoesNotExist:
        from django.contrib import messages
        messages.warning(request, 'No tienes un registro de empleado. Contacta con Recursos Humanos.')
        return redirect('inicio')

    context = {
        'empleado': empleado,
    }
    return render(request, 'asistencias/asistencias.html', context)


def calendar_events(request):
    """API que genera eventos para el calendario"""
    usuario_id = request.session.get('usuario_id')
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    if not all([usuario_id, start_str, end_str]):
        return JsonResponse([], safe=False)

    try:
        empleado = Empleados.objects.get(idusuarios_id=usuario_id)
    except Empleados.DoesNotExist:
        return JsonResponse([], safe=False)
    
    try:
        start_date = datetime.fromisoformat(start_str.split('T')[0]).date()
        end_date = datetime.fromisoformat(end_str.split('T')[0]).date()
    except Exception as e:
        return JsonResponse([], safe=False)

    # Obtener TODOS los horarios del empleado
    horarios = Horario.objects.filter(empleado=empleado).select_related('rol')
    
    # Obtener todas las asistencias en el rango
    asistencias = Asistencias.objects.filter(
        idempleado=empleado, 
        fechaasistencia__gte=start_date,
        fechaasistencia__lt=end_date
    ).select_related('rol')

    events = []
    
    # Mapear asistencias por fecha
    asistencias_map = defaultdict(list)
    for a in asistencias:
        asistencias_map[a.fechaasistencia].append(a)

    total_days = (end_date - start_date).days
    ahora = timezone.now()
    
    for day_offset in range(total_days):
        current_date = start_date + timedelta(days=day_offset)
        dia_semana_actual = current_date.weekday()
        semana_del_mes_actual = get_week_of_month(current_date)
        
        # Buscar TODOS los turnos programados para este día
        turnos_programados = [
            h for h in horarios 
            if h.dia_semana == dia_semana_actual and h.semana_del_mes == semana_del_mes_actual
        ]
        
        asistencias_del_dia = asistencias_map.get(current_date, [])
        asistencias_procesadas = set()

        # Procesar cada turno programado
        for turno in turnos_programados:
            rol = turno.rol
            
            # Crear fecha/hora inicio y fin del turno PROGRAMADO
            turno_inicio = timezone.make_aware(datetime.combine(current_date, turno.hora_inicio))
            turno_fin = timezone.make_aware(datetime.combine(current_date, turno.hora_fin))
            
            # Si el turno termina después de medianoche
            if turno.hora_fin < turno.hora_inicio:
                turno_fin += timedelta(days=1)
            
            # Buscar la asistencia que mejor coincida con este turno
            mejor_asistencia = None
            min_diff = float('inf')
            
            # Margen de búsqueda: desde 2 horas antes hasta el final del turno
            margen_inicio = turno_inicio - timedelta(hours=2)
            margen_fin = turno_fin

            for asistencia in asistencias_del_dia:
                if (asistencia.rol == rol and 
                    asistencia.idasistencia not in asistencias_procesadas and 
                    asistencia.horaentrada):
                    
                    hora_entrada_reg = timezone.make_aware(
                        datetime.combine(current_date, asistencia.horaentrada)
                    )
                    
                    # Verificar que esté dentro del margen
                    if margen_inicio <= hora_entrada_reg <= margen_fin:
                        diff = abs((hora_entrada_reg - turno_inicio).total_seconds())
                        if diff < min_diff:
                            min_diff = diff
                            mejor_asistencia = asistencia

            titulo = f"{rol.nombrerol if rol else 'Sin Rol'}"
            area = rol.nombrearea if rol else 'Sin Área'

            if mejor_asistencia:
                # HAY ASISTENCIA REGISTRADA
                asistencias_procesadas.add(mejor_asistencia.idasistencia)
                
                hora_entrada_real = timezone.make_aware(
                    datetime.combine(current_date, mejor_asistencia.horaentrada)
                )
                
                # CORRECCIÓN: Solo usar hora de salida si realmente existe
                if mejor_asistencia.horasalida:
                    hora_salida_real = timezone.make_aware(
                        datetime.combine(current_date, mejor_asistencia.horasalida)
                    )
                    if mejor_asistencia.horasalida < mejor_asistencia.horaentrada:
                        hora_salida_real += timedelta(days=1)
                else:
                    # Si no hay salida, usar la hora actual si es hoy y está en turno
                    # O usar la hora programada de fin si es día pasado
                    if current_date == timezone.localdate() and ahora < turno_fin:
                        hora_salida_real = ahora  # Está en turno AHORA
                    else:
                        hora_salida_real = turno_fin  # Usar hora programada
                
                # Calcular diferencia en MINUTOS
                diff_minutos = (hora_entrada_real - turno_inicio).total_seconds() / 60
                
                # Clasificación mejorada
                if diff_minutos <= -10:  # 10+ minutos antes
                    estado, className = ("Temprano", "event-temprano")
                elif -10 < diff_minutos <= 5:  # Entre -10 y +5 minutos
                    estado, className = ("Justo", "event-justo")
                elif 5 < diff_minutos <= 60:  # Entre +5 minutos y +1 hora
                    estado, className = ("Tarde", "event-tarde")
                else:  # Más de 1 hora tarde
                    estado, className = ("Muy Tarde", "event-ausente")

                events.append({
                    'title': titulo,
                    'start': hora_entrada_real.isoformat(),
                    'end': hora_salida_real.isoformat(),
                    'classNames': [className],
                    'extendedProps': {
                        'area': area,
                        'estado': estado,
                        'entrada_registrada': mejor_asistencia.horaentrada.strftime('%H:%M'),
                        'salida_registrada': mejor_asistencia.horasalida.strftime('%H:%M') if mejor_asistencia.horasalida else None,
                        'entrada_programada': turno.hora_inicio.strftime('%H:%M'),
                        'salida_programada': turno.hora_fin.strftime('%H:%M'),
                        'diferencia_minutos': round(diff_minutos, 1),
                        'en_turno': not mejor_asistencia.horasalida  # Flag para saber si está en turno
                    }
                })
            else:
                # NO HAY ASISTENCIA REGISTRADA
                event_data = {
                    'title': titulo,
                    'start': turno_inicio.isoformat(),
                    'end': turno_fin.isoformat(),
                    'extendedProps': {
                        'area': area,
                        'entrada_registrada': None,
                        'salida_registrada': None,
                        'entrada_programada': turno.hora_inicio.strftime('%H:%M'),
                        'salida_programada': turno.hora_fin.strftime('%H:%M'),
                        'en_turno': False
                    }
                }
                
                if current_date < timezone.localdate():
                    event_data['extendedProps']['estado'] = 'Ausente'
                    event_data['classNames'] = ['event-ausente']
                else:
                    event_data['extendedProps']['estado'] = 'Programado'
                    event_data['classNames'] = ['event-programado']
                
                events.append(event_data)

        # Procesar asistencias sin turno programado (fuera de turno)
        for asistencia in asistencias_del_dia:
            if asistencia.idasistencia not in asistencias_procesadas:
                titulo = f"{asistencia.rol.nombrerol if asistencia.rol else 'Sin Rol'}"
                area = asistencia.rol.nombrearea if asistencia.rol else 'Sin Área'
                
                if asistencia.horaentrada:
                    start_time = timezone.make_aware(
                        datetime.combine(current_date, asistencia.horaentrada)
                    )
                else:
                    continue
                
                if asistencia.horasalida:
                    end_time = timezone.make_aware(
                        datetime.combine(current_date, asistencia.horasalida)
                    )
                    if asistencia.horasalida < asistencia.horaentrada:
                        end_time += timedelta(days=1)
                else:
                    # Si es hoy y no tiene salida, usar hora actual
                    if current_date == timezone.localdate():
                        end_time = ahora
                    else:
                        end_time = start_time + timedelta(hours=8)
                
                events.append({
                    'title': titulo,
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'classNames': ['event-fuera-de-turno'],
                    'extendedProps': {
                        'area': area,
                        'estado': 'Fuera de Turno',
                        'entrada_registrada': asistencia.horaentrada.strftime('%H:%M'),
                        'salida_registrada': asistencia.horasalida.strftime('%H:%M') if asistencia.horasalida else None,
                        'entrada_programada': None,
                        'salida_programada': None,
                        'en_turno': not asistencia.horasalida
                    }
                })
    
    return JsonResponse(events, safe=False)