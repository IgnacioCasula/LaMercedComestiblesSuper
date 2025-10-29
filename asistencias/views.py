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

    # Validaciones
    if not all([usuario_id, start_str, end_str]):
        print("âŒ Faltan parÃ¡metros: usuario_id, start o end")
        return JsonResponse([], safe=False)

    try:
        empleado = Empleados.objects.get(idusuarios_id=usuario_id)
        print(f"âœ“ Empleado encontrado: {empleado}")
    except Empleados.DoesNotExist:
        print("âŒ Empleado no encontrado")
        return JsonResponse([], safe=False)
    
    # Parsear fechas
    try:
        start_date = datetime.fromisoformat(start_str.split('T')[0]).date()
        end_date = datetime.fromisoformat(end_str.split('T')[0]).date()
        print(f"âœ“ Rango de fechas: {start_date} a {end_date}")
    except Exception as e:
        print(f"âŒ Error parseando fechas: {e}")
        return JsonResponse([], safe=False)

    # Obtener horarios y asistencias
    horarios = Horario.objects.filter(empleado=empleado).select_related('rol')
    asistencias = Asistencias.objects.filter(
        idempleado=empleado, 
        fechaasistencia__gte=start_date,
        fechaasistencia__lt=end_date
    ).select_related('rol')

    print(f"âœ“ Horarios encontrados: {horarios.count()}")
    print(f"âœ“ Asistencias encontradas: {asistencias.count()}")

    events = []
    
    # Mapear asistencias por fecha
    asistencias_map = defaultdict(list)
    for a in asistencias:
        asistencias_map[a.fechaasistencia].append(a)
        print(f"  - Asistencia: {a.fechaasistencia} | Entrada: {a.horaentrada} | Salida: {a.horasalida} | Rol: {a.rol}")

    total_days = (end_date - start_date).days
    
    for day_offset in range(total_days):
        current_date = start_date + timedelta(days=day_offset)
        dia_semana_actual = current_date.weekday()  # 0=Lunes, 6=Domingo
        semana_del_mes_actual = get_week_of_month(current_date)
        
        # Buscar turnos programados para este dÃ­a
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
            
            # Si el turno termina despuÃ©s de medianoche
            if turno.hora_fin < turno.hora_inicio:
                turno_fin += timedelta(days=1)
            
            # Buscar la mejor asistencia que coincida con este turno
            mejor_asistencia = None
            min_diff = float('inf')
            margen_busqueda_inicio = turno_inicio - timedelta(hours=2)  # Margen de 2 horas antes

            for asistencia in asistencias_del_dia:
                # Verificar que coincida el rol y no estÃ© procesada
                if (asistencia.rol == rol and 
                    asistencia.idasistencia not in asistencias_procesadas and 
                    asistencia.horaentrada):
                    
                    hora_entrada_reg = timezone.make_aware(
                        datetime.combine(current_date, asistencia.horaentrada)
                    )
                    
                    # Verificar que estÃ© dentro del margen de bÃºsqueda
                    if hora_entrada_reg >= margen_busqueda_inicio:
                        diff = abs((hora_entrada_reg - turno_inicio).total_seconds())
                        if diff < min_diff:
                            min_diff = diff
                            mejor_asistencia = asistencia

            titulo = f"{rol.nombrerol if rol else 'Sin Rol'}"
            area = rol.nombrearea if rol else 'Sin Ãrea'

            if mejor_asistencia:
                # HAY ASISTENCIA REGISTRADA
                asistencias_procesadas.add(mejor_asistencia.idasistencia)
                
                # Usar la hora REAL de entrada registrada
                hora_entrada_real = timezone.make_aware(
                    datetime.combine(current_date, mejor_asistencia.horaentrada)
                )
                
                # Usar la hora REAL de salida si existe, sino usar la programada
                if mejor_asistencia.horasalida:
                    hora_salida_real = timezone.make_aware(
                        datetime.combine(current_date, mejor_asistencia.horasalida)
                    )
                    # Si la salida es antes que la entrada, es del dÃ­a siguiente
                    if mejor_asistencia.horasalida < mejor_asistencia.horaentrada:
                        hora_salida_real += timedelta(days=1)
                else:
                    # Si no hay hora de salida, usar la programada
                    hora_salida_real = turno_fin
                
                # Calcular puntualidad comparando entrada real vs programada
                diff_puntualidad = (hora_entrada_real - turno_inicio).total_seconds()
                
                if diff_puntualidad <= -600:  # -10 minutos o mÃ¡s temprano
                    estado, className = ("Temprano", "event-temprano")
                elif diff_puntualidad > 300:  # +5 minutos o mÃ¡s tarde
                    estado, className = ("Tarde", "event-tarde")
                else:  # Entre -10 y +5 minutos
                    estado, className = ("Justo", "event-justo")

                # MOSTRAR HORAS REALES, NO PROGRAMADAS
                events.append({
                    'title': titulo,
                    'start': hora_entrada_real.isoformat(),  # HORA REAL
                    'end': hora_salida_real.isoformat(),      # HORA REAL
                    'classNames': [className],
                    'extendedProps': {
                        'area': area,
                        'estado': estado,
                        'entrada_registrada': mejor_asistencia.horaentrada.strftime('%H:%M'),
                        'salida_registrada': mejor_asistencia.horasalida.strftime('%H:%M') if mejor_asistencia.horasalida else 'En turno',
                        'entrada_programada': turno.hora_inicio.strftime('%H:%M'),
                        'salida_programada': turno.hora_fin.strftime('%H:%M')
                    }
                })
            else:
                # NO HAY ASISTENCIA REGISTRADA - Mostrar turno programado
                event_data = {
                    'title': titulo,
                    'start': turno_inicio.isoformat(),
                    'end': turno_fin.isoformat(),
                    'extendedProps': {
                        'area': area,
                        'entrada_registrada': 'N/A',
                        'salida_registrada': 'N/A',
                        'entrada_programada': turno.hora_inicio.strftime('%H:%M'),
                        'salida_programada': turno.hora_fin.strftime('%H:%M')
                    }
                }
                
                if current_date < timezone.localdate():
                    # DÃ­a pasado sin asistencia = Ausente
                    event_data['extendedProps']['estado'] = 'Ausente'
                    event_data['classNames'] = ['event-ausente']
                else:
                    # DÃ­a futuro = Programado
                    event_data['extendedProps']['estado'] = 'Programado'
                    event_data['classNames'] = ['event-programado']
                
                events.append(event_data)

        # Procesar asistencias sin turno programado (fuera de turno)
        for asistencia in asistencias_del_dia:
            if asistencia.idasistencia not in asistencias_procesadas:
                titulo = f"{asistencia.rol.nombrerol if asistencia.rol else 'Sin Rol'}"
                area = asistencia.rol.nombrearea if asistencia.rol else 'Sin Ãrea'
                
                if asistencia.horaentrada:
                    start_time = timezone.make_aware(
                        datetime.combine(current_date, asistencia.horaentrada)
                    )
                else:
                    start_time = None
                
                # Calcular hora de fin
                if asistencia.horasalida:
                    end_time = timezone.make_aware(
                        datetime.combine(current_date, asistencia.horasalida)
                    )
                    if asistencia.horasalida < asistencia.horaentrada:
                        end_time += timedelta(days=1)
                else:
                    end_time = start_time + timedelta(hours=8) if start_time else None
                
                events.append({
                    'title': titulo,
                    'start': start_time.isoformat() if start_time else None,
                    'end': end_time.isoformat() if end_time else None,
                    'classNames': ['event-fuera-de-turno'],
                    'extendedProps': {
                        'area': area,
                        'estado': 'Fuera de Turno',
                        'entrada_registrada': asistencia.horaentrada.strftime('%H:%M') if asistencia.horaentrada else 'N/A',
                        'salida_registrada': asistencia.horasalida.strftime('%H:%M') if asistencia.horasalida else 'En turno'
                    }
                })
    
    print(f"âœ“ Total de eventos generados: {len(events)}")
    return JsonResponse(events, safe=False)