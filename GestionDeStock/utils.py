import json
import os
from datetime import datetime, timedelta
from django.conf import settings
import pandas as pd
from collections import defaultdict

# Crear directorio de logs si no existe
LOGS_DIR = os.path.join(settings.BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

def registrar_actividad(request, tipo_actividad, descripcion, detalles=None, nivel='INFO'):
    """
    Registra una actividad en archivo JSON (OPTIMIZADO - menos datos innecesarios)
    
    Args:
        request: HttpRequest object
        tipo_actividad: Tipo de actividad (LOGIN, LOGOUT, VENTA, etc.)
        descripcion: Descripción breve de la actividad
        detalles: Diccionario con información adicional relevante
        nivel: Nivel de importancia (INFO, WARNING, ERROR, CRITICAL)
    """
    try:
        usuario_id = request.session.get('usuario_id')
        nombre_usuario = request.session.get('nombre_usuario', 'Desconocido')
        
        # Obtener información del usuario (SOLO SI ES NECESARIO)
        area = None
        puesto = None
        
        if usuario_id and tipo_actividad in ['LOGIN', 'CREAR_EMPLEADO', 'EDITAR_EMPLEADO']:
            try:
                from .models import Usuarios, Roles
                usuario_obj = Usuarios.objects.get(idusuarios=usuario_id)
                rol = Roles.objects.filter(usuxroles__idusuarios=usuario_obj).first()
                if rol:
                    area = rol.nombrearea
                    puesto = rol.nombrerol
            except:
                pass
        
        # Obtener SOLO IP (sin User Agent largo)
        ip_address = get_client_ip(request)
        
        # Crear registro de log OPTIMIZADO
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'hora': datetime.now().strftime('%H:%M:%S'),
            'tipo_actividad': tipo_actividad,
            'nivel': nivel,
            'usuario_id': usuario_id,
            'nombre_usuario': nombre_usuario,
            'area': area,
            'puesto': puesto,
            'descripcion': descripcion,
            'detalles': detalles,  # Solo datos relevantes
            'ip_address': ip_address
            # ❌ ELIMINADO: user_agent (muy largo e innecesario)
        }
        
        # Guardar en archivo (un archivo por día)
        fecha_archivo = datetime.now().strftime('%Y-%m-%d')
        archivo_log = os.path.join(LOGS_DIR, f'actividad_{fecha_archivo}.jsonl')
        
        # Escribir en formato JSONL (una línea JSON por registro)
        with open(archivo_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        return True
        
    except Exception as e:
        print(f"Error registrando actividad: {e}")
        return False

def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def leer_logs(fecha_inicio=None, fecha_fin=None, tipo=None, nivel=None, usuario=None, search=None, limit=1000):
    """
    Lee y filtra logs desde los archivos
    
    Returns:
        list: Lista de logs que cumplen los criterios
    """
    try:
        logs = []
        
        # Si no hay fecha de inicio, usar últimos 7 días
        if not fecha_inicio:
            fecha_inicio = (datetime.now() - timedelta(days=7)).date()
        else:
            if isinstance(fecha_inicio, str):
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        
        if not fecha_fin:
            fecha_fin = datetime.now().date()
        else:
            if isinstance(fecha_fin, str):
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        # Leer archivos en el rango de fechas
        current_date = fecha_inicio
        while current_date <= fecha_fin:
            archivo_log = os.path.join(LOGS_DIR, f'actividad_{current_date.strftime("%Y-%m-%d")}.jsonl')
            
            if os.path.exists(archivo_log):
                with open(archivo_log, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            log = json.loads(line.strip())
                            
                            # Aplicar filtros
                            if tipo and log.get('tipo_actividad') != tipo:
                                continue
                            
                            if nivel and log.get('nivel') != nivel:
                                continue
                            
                            if usuario and log.get('nombre_usuario') != usuario:
                                continue
                            
                            if search:
                                search_lower = search.lower()
                                searchable_fields = [
                                    str(log.get('nombre_usuario', '')),
                                    str(log.get('descripcion', '')),
                                    str(log.get('tipo_actividad', '')),
                                    str(log.get('area', '')),
                                    str(log.get('puesto', ''))
                                ]
                                if not any(search_lower in field.lower() for field in searchable_fields):
                                    continue
                            
                            logs.append(log)
                            
                        except json.JSONDecodeError:
                            continue
            
            current_date += timedelta(days=1)
        
        # Ordenar por timestamp descendente (más recientes primero)
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Limitar resultados
        return logs[:limit]
        
    except Exception as e:
        print(f"Error leyendo logs: {e}")
        return []

def obtener_estadisticas_logs(dias=7):
    """
    Obtiene estadísticas ÚTILES de los logs usando Pandas
    
    Returns:
        dict: Diccionario con estadísticas que responden preguntas de negocio
    """
    try:
        fecha_inicio = (datetime.now() - timedelta(days=dias)).date()
        logs = leer_logs(fecha_inicio=fecha_inicio, limit=100000)
        
        if not logs:
            return _estadisticas_vacias()
        
        # Convertir a DataFrame de Pandas
        df = pd.DataFrame(logs)
        
        # Asegurar tipos de datos correctos
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['hora_int'] = pd.to_datetime(df['hora'], format='%H:%M:%S').dt.hour
        
        # ==========================================
        # 📊 ESTADÍSTICA 1: Actividad por hora del día
        # Pregunta: ¿A qué horas hay más actividad en el sistema?
        # ==========================================
        actividad_por_hora = df.groupby('hora_int').size().reset_index(name='total')
        actividad_por_hora = actividad_por_hora.sort_values('hora_int')
        actividad_por_hora['hora_label'] = actividad_por_hora['hora_int'].apply(lambda x: f"{x:02d}:00")
        
        # ==========================================
        # 📊 ESTADÍSTICA 2: Rendimiento de ventas por usuario
        # Pregunta: ¿Quién vende más? ¿Cuánto genera cada vendedor?
        # ==========================================
        ventas_df = df[df['tipo_actividad'] == 'VENTA'].copy()
        
        if len(ventas_df) > 0:
            # Extraer el total de venta de los detalles
            ventas_df['monto'] = ventas_df['detalles'].apply(
                lambda x: float(x.get('total', 0)) if isinstance(x, dict) else 0
            )
            
            ventas_por_usuario = ventas_df.groupby('nombre_usuario').agg({
                'monto': ['sum', 'count', 'mean']
            }).reset_index()
            
            ventas_por_usuario.columns = ['usuario', 'total_vendido', 'cantidad_ventas', 'ticket_promedio']
            ventas_por_usuario = ventas_por_usuario.sort_values('total_vendido', ascending=False).head(10)
        else:
            ventas_por_usuario = pd.DataFrame(columns=['usuario', 'total_vendido', 'cantidad_ventas', 'ticket_promedio'])
        
        # ==========================================
        # 📊 ESTADÍSTICA 3: Problemas de caja (diferencias)
        # Pregunta: ¿Qué cajas tienen más diferencias? ¿Hay patrones?
        # ==========================================
        cierres_df = df[df['tipo_actividad'] == 'CIERRE_CAJA'].copy()
        
        if len(cierres_df) > 0:
            cierres_df['diferencia'] = cierres_df['detalles'].apply(
                lambda x: float(x.get('diferencia', 0)) if isinstance(x, dict) else 0
            )
            
            problemas_caja = cierres_df.groupby('nombre_usuario').agg({
                'diferencia': ['sum', 'count', 'mean', 'std']
            }).reset_index()
            
            problemas_caja.columns = ['usuario', 'diferencia_total', 'cantidad_cierres', 'diferencia_promedio', 'desviacion']
            problemas_caja['tiene_problemas'] = problemas_caja['diferencia_promedio'].abs() > 10
            problemas_caja = problemas_caja.sort_values('diferencia_total', ascending=False).head(10)
        else:
            problemas_caja = pd.DataFrame(columns=['usuario', 'diferencia_total', 'cantidad_cierres', 'diferencia_promedio'])
        
        # ==========================================
        # 📊 ESTADÍSTICA 4: Puntualidad de empleados
        # Pregunta: ¿Quiénes llegan tarde más frecuentemente?
        # ==========================================
        logins_df = df[df['tipo_actividad'] == 'LOGIN'].copy()
        
        if len(logins_df) > 0:
            # Extraer hora de login
            logins_df['hora_login'] = pd.to_datetime(logins_df['hora'], format='%H:%M:%S').dt.hour * 60 + \
                                       pd.to_datetime(logins_df['hora'], format='%H:%M:%S').dt.minute
            
            # Considerar "tarde" después de las 8:00 AM (480 minutos)
            logins_df['llego_tarde'] = logins_df['hora_login'] > 480
            
            puntualidad = logins_df.groupby('nombre_usuario').agg({
                'llego_tarde': ['sum', 'count']
            }).reset_index()
            
            puntualidad.columns = ['usuario', 'veces_tarde', 'total_logins']
            puntualidad['porcentaje_tardanzas'] = (puntualidad['veces_tarde'] / puntualidad['total_logins'] * 100).round(1)
            puntualidad = puntualidad[puntualidad['total_logins'] >= 3]  # Solo usuarios con al menos 3 logins
            puntualidad = puntualidad.sort_values('porcentaje_tardanzas', ascending=False).head(10)
        else:
            puntualidad = pd.DataFrame(columns=['usuario', 'veces_tarde', 'total_logins', 'porcentaje_tardanzas'])
        
        # ==========================================
        # 📊 ESTADÍSTICA 5: Tendencia de actividad por día
        # Pregunta: ¿La actividad está aumentando o disminuyendo?
        # ==========================================
        actividad_diaria = df.groupby('fecha').size().reset_index(name='total')
        actividad_diaria = actividad_diaria.sort_values('fecha')
        actividad_diaria['fecha_str'] = actividad_diaria['fecha'].dt.strftime('%Y-%m-%d')
        
        # ==========================================
        # 📊 ESTADÍSTICA 6: Errores y problemas críticos
        # Pregunta: ¿Qué errores críticos estamos teniendo?
        # ==========================================
        errores_df = df[df['nivel'].isin(['ERROR', 'CRITICAL'])].copy()
        
        if len(errores_df) > 0:
            errores_por_tipo = errores_df.groupby('tipo_actividad').size().reset_index(name='total')
            errores_por_tipo = errores_por_tipo.sort_values('total', ascending=False)
            
            errores_recientes = errores_df.nlargest(10, 'timestamp')[
                ['timestamp', 'tipo_actividad', 'nombre_usuario', 'descripcion', 'nivel']
            ].to_dict('records')
        else:
            errores_por_tipo = pd.DataFrame(columns=['tipo_actividad', 'total'])
            errores_recientes = []
        
        # ==========================================
        # RETORNAR ESTADÍSTICAS
        # ==========================================
        return {
            # 1. Actividad por hora
            'actividad_por_hora': actividad_por_hora.to_dict('records'),
            
            # 2. Rendimiento de ventas
            'ventas_por_usuario': ventas_por_usuario.to_dict('records'),
            
            # 3. Problemas de caja
            'problemas_caja': problemas_caja.to_dict('records'),
            
            # 4. Puntualidad
            'puntualidad_empleados': puntualidad.to_dict('records'),
            
            # 5. Tendencia diaria
            'actividad_diaria': actividad_diaria.to_dict('records'),
            
            # 6. Errores críticos
            'errores_por_tipo': errores_por_tipo.to_dict('records'),
            'errores_recientes': errores_recientes,
            
            # Resumen general
            'resumen': {
                'total_actividades': len(df),
                'total_usuarios_activos': df['nombre_usuario'].nunique(),
                'total_ventas': len(ventas_df),
                'monto_total_ventas': float(ventas_df['monto'].sum()) if len(ventas_df) > 0 else 0,
                'total_errores': len(errores_df),
                'periodo_dias': dias
            }
        }
        
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        import traceback
        traceback.print_exc()
        return _estadisticas_vacias()

def _estadisticas_vacias():
    """Retorna estructura vacía de estadísticas"""
    return {
        'actividad_por_hora': [],
        'ventas_por_usuario': [],
        'problemas_caja': [],
        'puntualidad_empleados': [],
        'actividad_diaria': [],
        'errores_por_tipo': [],
        'errores_recientes': [],
        'resumen': {
            'total_actividades': 0,
            'total_usuarios_activos': 0,
            'total_ventas': 0,
            'monto_total_ventas': 0,
            'total_errores': 0,
            'periodo_dias': 7
        }
    }