from datetime import timedelta
import random
import json
import string

from django.shortcuts import render, redirect
from django.utils import timezone
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from .utils import registrar_actividad

from datetime import datetime, time
from caja.models import (
    Usuarios, Roles, UsuxRoles, Empleados, Horario, Caja, Asistencias
)

MAX_INTENTOS = 3
BLOQUEO_MINUTOS = 5
CODIGO_EXPIRA_MINUTOS = 5


def _verificar_y_restaurar_sesion_gracia(request):
    """
    Verifica si el usuario está dentro del período de gracia de 2 minutos
    y restaura la sesión sin registrar salida.
    
    Retorna el usuario_id si está en período de gracia, None si no.
    """
    try:
        grace_cookie = request.get_signed_cookie(
            'grace_logout',
            default=None,
            salt='logout-grace',
            max_age=130
        )
        
        if grace_cookie:
            # Parsear cookie: formato "usuario_id|timestamp_iso"
            parts = grace_cookie.split('|')
            if len(parts) == 2:
                usuario_id, expira_str = parts
                try:
                    expira = timezone.datetime.fromisoformat(expira_str)
                    if timezone.is_naive(expira):
                        expira = timezone.make_aware(expira)
                    
                    ahora = timezone.now()
                    
                    # Verificar si aún está dentro del período de gracia
                    if ahora < expira:
                        print(f"✅ Usuario {usuario_id} dentro del período de gracia")
                        
                        # ELIMINAR el registro de salida de hoy
                        try:
                            empleado = Empleados.objects.get(idusuarios_id=usuario_id)
                            hoy = timezone.localdate()
                            
                            asistencia = Asistencias.objects.filter(
                                idempleado=empleado,
                                fechaasistencia=hoy,
                                horasalida__isnull=False  # Que tenga salida registrada
                            ).order_by('-horasalida').first()
                            
                            if asistencia:
                                # Eliminar la hora de salida
                                asistencia.horasalida = None
                                asistencia.save()
                                print(f"✅ Salida eliminada para usuario {usuario_id}")
                        except Exception as e:
                            print(f"⚠️ Error al eliminar salida: {e}")
                        
                        return usuario_id
                    else:
                        print(f"⏰ Período de gracia expirado para usuario {usuario_id}")
                except Exception as e:
                    print(f"⚠️ Error parseando cookie de gracia: {e}")
        
    except Exception as e:
        print(f"⚠️ Error verificando período de gracia: {e}")
    
    return None


def _registrar_entrada_automatica(usuario_id):
    """
    Registra automáticamente la entrada de un empleado al hacer login.
    Retorna True si se registró, False si ya tenía entrada.
    """
    try:
        empleado = Empleados.objects.get(idusuarios_id=usuario_id)
        hoy = timezone.localdate()
        
        # Verificar si ya tiene entrada hoy
        asistencia_hoy = Asistencias.objects.filter(
            idempleado=empleado,
            fechaasistencia=hoy
        ).first()
        
        if asistencia_hoy:
            # Ya tiene entrada registrada hoy
            return False
        
        # Obtener el rol actual del usuario
        rol = Roles.objects.filter(usuxroles__idusuarios_id=usuario_id).first()
        
        # Crear registro de asistencia (entrada)
        hora_actual = timezone.localtime().time()
        Asistencias.objects.create(
            idempleado=empleado,
            fechaasistencia=hoy,
            horaentrada=hora_actual,
            horasalida=None,  # Sin salida todavía
            rol=rol
        )
        
        print(f"✅ Entrada automática registrada: {empleado.idusuarios.nombreusuario} a las {hora_actual}")
        return True
        
    except Empleados.DoesNotExist:
        # Si no es empleado (ej: admin sin registro), no hacer nada
        return False
    except Exception as e:
        print(f"❌ Error registrando entrada automática: {e}")
        return False


def _registrar_salida_automatica(usuario_id):
    """
    Registra automáticamente la salida de un empleado al hacer logout.
    Retorna True si se registró, False si no había entrada o ya tenía salida.
    """
    try:
        empleado = Empleados.objects.get(idusuarios_id=usuario_id)
        hoy = timezone.localdate()
        
        # Buscar la asistencia de hoy sin salida registrada
        asistencia = Asistencias.objects.filter(
            idempleado=empleado,
            fechaasistencia=hoy,
            horasalida__isnull=True
        ).first()
        
        if not asistencia:
            # No hay entrada registrada hoy o ya registró su salida
            return False
        
        # Registrar hora de salida
        hora_actual = timezone.localtime().time()
        asistencia.horasalida = hora_actual
        asistencia.save()
        
        print(f"✅ Salida automática registrada: {empleado.idusuarios.nombreusuario} a las {hora_actual}")
        return True
        
    except Empleados.DoesNotExist:
        return False
    except Exception as e:
        print(f"❌ Error registrando salida automática: {e}")
        return False


def _verificar_autenticacion(request: HttpRequest) -> bool:
    """Verifica si el usuario está autenticado"""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return False
    
    usuario = Usuarios.objects.filter(idusuarios=usuario_id).first()
    return usuario is not None


def _verificar_estado_empleado(request: HttpRequest) -> tuple[bool, str]:
    """Verifica si el empleado tiene un estado válido"""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return False, 'No hay sesión activa.'
    
    try:
        usuario = Usuarios.objects.filter(idusuarios=usuario_id).first()
        if not usuario:
            return False, 'Usuario no encontrado.'
        
        empleado = Empleados.objects.get(idusuarios=usuario)
        
        if empleado.estado == 'Suspendido':
            return False, 'Tu cuenta ha sido suspendida temporalmente. Contacta con Recursos Humanos.'
        elif empleado.estado == 'Despedido':
            return False, 'Tu cuenta ha sido desactivada. Contacta con Recursos Humanos.'
        
        return True, ''
        
    except Empleados.DoesNotExist:
        return True, ''
    except Exception as e:
        print(f"Error verificando estado del empleado: {e}")
        return True, ''


@require_http_methods(['POST'])
def registrar_entrada(request):
    """Registra la entrada de un empleado"""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    try:
        empleado = Empleados.objects.get(idusuarios_id=usuario_id)
        
        # Verificar si ya tiene entrada hoy
        hoy = timezone.localdate()
        asistencia_hoy = Asistencias.objects.filter(
            idempleado=empleado,
            fechaasistencia=hoy,
            horasalida__isnull=True
        ).first()
        
        if asistencia_hoy:
            return JsonResponse({
                'error': 'Ya registraste tu entrada hoy',
                'hora_entrada': asistencia_hoy.horaentrada.strftime('%H:%M')
            }, status=400)
        
        # Obtener el rol actual del usuario
        rol = Roles.objects.filter(usuxroles__idusuarios_id=usuario_id).first()
        
        # Crear registro de asistencia
        hora_actual = timezone.localtime().time()
        asistencia = Asistencias.objects.create(
            idempleado=empleado,
            fechaasistencia=hoy,
            horaentrada=hora_actual,
            rol=rol
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Entrada registrada correctamente',
            'hora': hora_actual.strftime('%H:%M'),
            'fecha': hoy.strftime('%d/%m/%Y')
        })
        
    except Empleados.DoesNotExist:
        return JsonResponse({'error': 'Empleado no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
def registrar_salida(request):
    """Registra la salida de un empleado"""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    try:
        empleado = Empleados.objects.get(idusuarios_id=usuario_id)
        
        # Buscar la asistencia de hoy sin salida registrada
        hoy = timezone.localdate()
        asistencia = Asistencias.objects.filter(
            idempleado=empleado,
            fechaasistencia=hoy,
            horasalida__isnull=True
        ).first()
        
        if not asistencia:
            return JsonResponse({
                'error': 'No hay entrada registrada hoy o ya registraste tu salida'
            }, status=400)
        
        # Registrar hora de salida
        hora_actual = timezone.localtime().time()
        asistencia.horasalida = hora_actual
        asistencia.save()
        
        # Calcular horas trabajadas
        entrada_dt = datetime.combine(hoy, asistencia.horaentrada)
        salida_dt = datetime.combine(hoy, hora_actual)
        horas_trabajadas = (salida_dt - entrada_dt).total_seconds() / 3600
        
        return JsonResponse({
            'success': True,
            'message': 'Salida registrada correctamente',
            'hora_entrada': asistencia.horaentrada.strftime('%H:%M'),
            'hora_salida': hora_actual.strftime('%H:%M'),
            'horas_trabajadas': round(horas_trabajadas, 2)
        })
        
    except Empleados.DoesNotExist:
        return JsonResponse({'error': 'Empleado no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['GET'])
def estado_asistencia_hoy(request):
    """Obtiene el estado de la asistencia del día de hoy"""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    try:
        empleado = Empleados.objects.get(idusuarios_id=usuario_id)
        hoy = timezone.localdate()
        
        asistencia = Asistencias.objects.filter(
            idempleado=empleado,
            fechaasistencia=hoy
        ).first()
        
        if not asistencia:
            return JsonResponse({
                'tiene_entrada': False,
                'tiene_salida': False
            })
        
        return JsonResponse({
            'tiene_entrada': True,
            'tiene_salida': asistencia.horasalida is not None,
            'hora_entrada': asistencia.horaentrada.strftime('%H:%M') if asistencia.horaentrada else None,
            'hora_salida': asistencia.horasalida.strftime('%H:%M') if asistencia.horasalida else None
        })
        
    except Empleados.DoesNotExist:
        return JsonResponse({'error': 'Empleado no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def _get_session_dict(request: HttpRequest, key: str, default: dict) -> dict:
    data = request.session.get(key)
    if not isinstance(data, dict):
        data = default.copy()
        request.session[key] = data
    return data


def _get_caja_abierta(usuario_id):
    """Verifica si hay una caja abierta para el usuario actual"""
    try:
        from datetime import time
        caja_abierta = Caja.objects.filter(
            idusuarios_id=usuario_id,
            horacierrecaja=time(0, 0, 0)  # Caja abierta (indicador de no cerrada)
        ).exists()
        return caja_abierta
    except Exception as e:
        print(f"Error verificando caja: {e}")
        return False


def login_view(request: HttpRequest) -> HttpResponse:
    # 🔥 VERIFICAR PERÍODO DE GRACIA PRIMERO
    usuario_en_gracia = _verificar_y_restaurar_sesion_gracia(request)
    if usuario_en_gracia:
        # Restaurar sesión automáticamente
        request.session['usuario_id'] = int(usuario_en_gracia)
        usuario = Usuarios.objects.get(idusuarios=int(usuario_en_gracia))
        request.session['nombre_usuario'] = usuario.nombreusuario
        
        # Obtener roles
        roles_ids = list(UsuxRoles.objects.filter(idusuarios=usuario).values_list('idroles', flat=True))
        if len(roles_ids) <= 1:
            if roles_ids:
                request.session['rol_id'] = roles_ids[0]
        
        # Limpiar cookie de gracia
        respuesta = redirect('inicio')
        respuesta.delete_cookie('grace_logout')
        
        messages.success(request, '¡Bienvenido de vuelta! Tu sesión fue restaurada y continúas en turno.')
        return respuesta
    
    estado = _get_session_dict(request, 'login_estado', {
        'intentos': 0,
        'bloqueado_hasta': None,
    })

    ahora = timezone.now()
    bloqueado_hasta = estado.get('bloqueado_hasta')
    if isinstance(bloqueado_hasta, str):
        try:
            bloqueado_hasta = timezone.datetime.fromisoformat(bloqueado_hasta)
        except Exception:
            bloqueado_hasta = None
    if bloqueado_hasta is not None and timezone.is_naive(bloqueado_hasta):
        try:
            bloqueado_hasta = timezone.make_aware(bloqueado_hasta)
        except Exception:
            pass
    if bloqueado_hasta and ahora < bloqueado_hasta:
        restante = int((bloqueado_hasta - ahora).total_seconds() // 1)
        contexto = {'bloqueado': True, 'segundos_restantes': max(restante, 0)}
        return render(request, 'HTML/login.html', contexto)

    if request.method == 'POST':
        usuario_o_email = request.POST.get('usuario_email', '').strip()
        password = request.POST.get('password', '')

        try:
            usuario = Usuarios.objects.filter(emailusuario=usuario_o_email).first()
            if not usuario:
                usuario = Usuarios.objects.filter(nombreusuario=usuario_o_email).first()
        except Exception:
            usuario = None

        autenticado = False
        if usuario:
            autenticado = usuario.passwordusuario == password

        if not autenticado:
            estado['intentos'] = int(estado.get('intentos', 0)) + 1
            if estado['intentos'] >= MAX_INTENTOS:
                estado['bloqueado_hasta'] = (ahora + timedelta(minutes=BLOQUEO_MINUTOS)).isoformat()
                request.session['login_estado'] = estado
                messages.error(request, 'Se acabaron los intentos. Intenta nuevamente en 5 minutos.')
                return redirect('login')

            request.session['login_estado'] = estado
            messages.error(request, f'Credenciales inválidas. Intento {estado["intentos"]} de {MAX_INTENTOS}.')
            return redirect('login')

        # Verificar estado del empleado
        try:
            empleado = Empleados.objects.get(idusuarios=usuario)
            
            if empleado.estado == 'Suspendido':
                messages.error(request, 'Tu cuenta ha sido suspendida temporalmente. Contacta con Recursos Humanos.')
                return redirect('login')
            elif empleado.estado == 'Despedido':
                messages.error(request, 'Tu cuenta ha sido desactivada. Contacta con Recursos Humanos.')
                return redirect('login')
            
        except Empleados.DoesNotExist:
            pass

        # ✅ Autenticación exitosa
        estado['intentos'] = 0
        estado['bloqueado_hasta'] = None
        request.session['login_estado'] = estado

        request.session['usuario_id'] = usuario.idusuarios
        request.session['nombre_usuario'] = usuario.nombreusuario

        registrar_actividad(
            request,
            'LOGIN',
            f'Usuario {usuario.nombreusuario} inició sesión',
            detalles={'usuario_id': usuario.idusuarios}
        )

        # 🔥 REGISTRAR ENTRADA AUTOMÁTICA
        entrada_registrada = _registrar_entrada_automatica(usuario.idusuarios)
        if entrada_registrada:
            messages.success(request, f'¡Bienvenido! Tu entrada fue registrada a las {timezone.localtime().strftime("%H:%M")}')

        roles_ids = list(UsuxRoles.objects.filter(idusuarios=usuario).values_list('idroles', flat=True))
        if len(roles_ids) <= 1:
            if roles_ids:
                request.session['rol_id'] = roles_ids[0]
            return redirect('inicio')
        else:
            return redirect('seleccionar_rol')

    return render(request, 'HTML/login.html')


def enviar_codigo_view(request: HttpRequest) -> HttpResponse:
    email_entrada = request.POST.get('usuario_email', '').strip()

    if not email_entrada:
        return render(request, 'HTML/solicitar_usuario.html')

    usuario = Usuarios.objects.filter(emailusuario=email_entrada).first()
    if not usuario:
        return render(request, 'HTML/solicitar_usuario.html', {'email_prefill': email_entrada, 'no_existe': True})

    _generar_y_enviar_codigo(request, destino=email_entrada)
    request.session['recuperacion_email'] = email_entrada
    return redirect('ingresar_codigo')


def reenviar_codigo_view(request: HttpRequest) -> HttpResponse:
    destino = request.session.get('recuperacion_email')
    if not destino:
        messages.error(request, 'Primero solicita un código.')
        return redirect('login')
    _generar_y_enviar_codigo(request, destino)
    messages.success(request, 'Nuevo código enviado.')
    return redirect('ingresar_codigo')


def ingresar_codigo_view(request: HttpRequest) -> HttpResponse:
    datos = _get_session_dict(request, 'codigo_estado', {})
    expira = datos.get('expira')
    if isinstance(expira, str):
        try:
            expira = timezone.datetime.fromisoformat(expira)
        except Exception:
            expira = None
    if expira is not None and timezone.is_naive(expira):
        try:
            expira = timezone.make_aware(expira)
        except Exception:
            pass
    ahora = timezone.now()
    expirado = expira and (ahora > expira)

    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo', '').strip()
        if not codigo_ingresado:
            messages.error(request, 'Ingresa el código de 5 dígitos.')
            return redirect('ingresar_codigo')

        if not expirado and codigo_ingresado == datos.get('codigo'):
            return redirect('cambiar_contrasena')
        else:
            messages.error(request, 'Código incorrecto o vencido.')
            return redirect('ingresar_codigo')

    contexto = {
        'expirado': bool(expirado),
        'segundos_restantes': int((expira - ahora).total_seconds()) if expira and not expirado else 0,
        'destino': request.session.get('recuperacion_email')
    }
    return render(request, 'HTML/ingresar_codigo.html', contexto)


def cambiar_contrasena_view(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        nueva = request.POST.get('nueva', '')
        repetir = request.POST.get('repetir', '')
        if len(nueva) < 6:
            messages.error(request, 'La contraseña debe tener más de 5 dígitos.')
            return redirect('cambiar_contrasena')
        if nueva != repetir:
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('cambiar_contrasena')

        email = request.session.get('recuperacion_email')
        if not email:
            messages.error(request, 'Sesión de recuperación no encontrada.')
            return redirect('login')
        usuario = Usuarios.objects.filter(emailusuario=email).first()
        if not usuario:
            messages.error(request, 'Usuario no encontrado.')
            return redirect('login')
        usuario.passwordusuario = nueva
        usuario.save(update_fields=['passwordusuario'])
        messages.success(request, 'Contraseña actualizada correctamente.')
        return redirect('login')

    return render(request, 'HTML/cambiar_contrasena.html')


def seleccionar_rol_view(request: HttpRequest) -> HttpResponse:
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')
    usuario = Usuarios.objects.filter(idusuarios=usuario_id).first()
    if not usuario:
        return redirect('login')

    if request.method == 'POST':
        rol_id = request.POST.get('rol_id')
        if rol_id and UsuxRoles.objects.filter(idusuarios=usuario, idroles_id=rol_id).exists():
            request.session['rol_id'] = int(rol_id)
            return redirect('inicio')
        messages.error(request, 'Selecciona un rol válido.')

    roles_usuario = Roles.objects.filter(usuxroles__idusuarios=usuario).order_by('nombrearea', 'nombrerol')
    return render(request, 'HTML/seleccionar_rol.html', {'roles': roles_usuario})


def inicio_view(request: HttpRequest) -> HttpResponse:
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
        return redirect('login')
    
    nombre_usuario = request.session.get('nombre_usuario', 'Usuario')
    rol_id = request.session.get('rol_id')
    
    usuario = Usuarios.objects.filter(idusuarios=usuario_id).first()
    if not usuario:
        messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
        return redirect('login')
    
    # VALIDACIÓN: Verificar estado del empleado en tiempo real
    try:
        empleado = Empleados.objects.get(idusuarios=usuario)
        
        if empleado.estado == 'Suspendido':
            request.session.flush()
            messages.error(request, 'Tu cuenta ha sido suspendida. Contacta con Recursos Humanos.')
            return redirect('login')
        elif empleado.estado == 'Despedido':
            request.session.flush()
            messages.error(request, 'Tu cuenta ha sido desactivada. Contacta con Recursos Humanos.')
            return redirect('login')
            
    except Empleados.DoesNotExist:
        pass
    
    # Obtener todos los roles del usuario
    roles_usuario = Roles.objects.filter(usuxroles__idusuarios_id=usuario_id)
    
    # Determinar si es administrador
    is_admin = any(
        'administrador' in rol.nombrerol.lower() or 
        'recursos humanos' in rol.nombrerol.lower() or
        'rrhh' in rol.nombrerol.lower()
        for rol in roles_usuario
    ) or roles_usuario.count() > 2
    
    # Extraer permisos de todos los roles del usuario
    permisos_usuario = set()
    
    for rol in roles_usuario:
        nombre_rol_lower = rol.nombrerol.lower()
        descripcion_rol_lower = (rol.descripcionrol or '').lower()
        
        # Permisos basados en el nombre del rol
        if 'vendedor' in nombre_rol_lower or 'registrar venta' in nombre_rol_lower:
            permisos_usuario.add('registrar_venta')
            permisos_usuario.add('caja')
        
        if 'caja' in nombre_rol_lower or 'cajero' in nombre_rol_lower:
            permisos_usuario.add('caja')
        
        if 'stock' in nombre_rol_lower or 'inventario' in nombre_rol_lower:
            permisos_usuario.add('stock')
        
        if 'supervisor' in nombre_rol_lower:
            permisos_usuario.add('asistencias')
        
        # Permisos basados en la descripción del rol
        if 'caja' in descripcion_rol_lower:
            permisos_usuario.add('caja')
        
        if 'stock' in descripcion_rol_lower:
            permisos_usuario.add('stock')
        
        if 'crear_empleado' in descripcion_rol_lower or 'crear empleado' in descripcion_rol_lower:
            permisos_usuario.add('crear_empleado')
        
        if 'asistencias' in descripcion_rol_lower:
            permisos_usuario.add('asistencias')
        
        if 'registrar_venta' in descripcion_rol_lower or 'registrar venta' in descripcion_rol_lower:
            permisos_usuario.add('registrar_venta')
            permisos_usuario.add('caja')
    
    # Si es admin, tiene todos los permisos
    if is_admin:
        has_caja = True
        has_registrar_venta = True
        has_gestion_stock = True
    else:
        has_caja = 'caja' in permisos_usuario
        has_registrar_venta = 'registrar_venta' in permisos_usuario or 'caja' in permisos_usuario
        has_gestion_stock = 'stock' in permisos_usuario
    
    # Verificar estado de la caja
    caja_abierta = _get_caja_abierta(usuario_id)
    
    # Obtener nombre del rol actual
    rol_actual = None
    if rol_id:
        rol_obj = Roles.objects.filter(idroles=rol_id).first()
        if rol_obj:
            rol_actual = rol_obj.nombrerol
    
    context = {
        'nombre_usuario': nombre_usuario,
        'rol_nombre': rol_actual,
        'is_admin': is_admin,
        'has_caja': has_caja,
        'has_registrar_venta': has_registrar_venta,
        'has_gestion_stock': has_gestion_stock,
        'caja_abierta': caja_abierta,
        'debug_roles': list(roles_usuario.values_list('nombrerol', flat=True)),
        'debug_permisos': list(permisos_usuario),
    }
    return render(request, 'HTML/inicio.html', context)


@require_http_methods(['GET'])
def api_caja_status(request: HttpRequest) -> JsonResponse:
    """API para obtener el estado actual de la caja"""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    caja_abierta = _get_caja_abierta(usuario_id)
    return JsonResponse({'abierta': caja_abierta})


def logout_view(request: HttpRequest) -> HttpResponse:
    """Cierra la sesión y registra la salida automática."""
    usuario_id = request.session.get('usuario_id')
    respuesta = redirect('login')

    if usuario_id:
        # 🔥 REGISTRAR SALIDA AUTOMÁTICA ANTES DE CERRAR SESIÓN
        registrar_actividad(
            request,
            'LOGOUT',
            'Usuario cerró sesión',
            detalles={'usuario_id': usuario_id}
        )
        salida_registrada = _registrar_salida_automatica(usuario_id)
        if salida_registrada:
            print(f"✅ Salida registrada automáticamente para usuario {usuario_id}")
        
        # Período de gracia de 2 minutos
        expira = timezone.now() + timedelta(minutes=2)
        valor = f"{usuario_id}|{expira.isoformat()}"
        respuesta.set_signed_cookie(
            key='grace_logout',
            value=valor,
            salt='logout-grace',
            max_age=130,  # 2 minutos + 10 segundos de margen
            httponly=True,
            samesite='Lax',
        )
        
        messages.info(request, 'Sesión cerrada. Tienes 2 minutos para volver sin que se registre tu salida.')

    try:
        request.session.flush()
    except Exception:
        request.session.clear()

    return respuesta


def crear_empleado_view(request: HttpRequest) -> HttpResponse:
    """Vista para crear un nuevo empleado."""
    if not _verificar_autenticacion(request):
        messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
        return redirect('login')
    
    es_valido, mensaje_error = _verificar_estado_empleado(request)
    if not es_valido:
        request.session.flush()
        messages.error(request, mensaje_error)
        return redirect('login')
    
    usuario_id = request.session.get('usuario_id')
    usuario = Usuarios.objects.filter(idusuarios=usuario_id).first()
    
    if not usuario:
        messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
        return redirect('login')
    
    roles_usuario = list(
        Roles.objects.filter(usuxroles__idusuarios_id=usuario_id).values_list('nombrerol', flat=True)
    )
    
    is_admin = 'Administrador' in roles_usuario or 'Recursos Humanos' in roles_usuario
    
    if not is_admin:
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('inicio')
    
    return render(request, 'HTML/crear_empleado.html')


def api_areas(request):
    """Devuelve todas las áreas."""
    query = request.GET.get('q', '').strip()
    if query:
        areas = Roles.objects.filter(nombrearea__icontains=query).values('nombrearea').distinct()
    else:
        areas = Roles.objects.values('nombrearea').distinct()
    
    data = [{'id': area['nombrearea'], 'nombre': area['nombrearea']} for area in areas]
    return JsonResponse(data, safe=False)


def api_areas_puestos(request):
    """Devuelve todas las áreas con sus puestos, permisos y salarios."""
    try:
        areas = Roles.objects.values('nombrearea').distinct().order_by('nombrearea')
        
        resultado = []
        for area in areas:
            area_nombre = area['nombrearea']
            puestos = Roles.objects.filter(
                nombrearea=area_nombre
            ).exclude(
                nombrerol__startswith='_placeholder_'
            ).order_by('nombrerol')
            
            puestos_data = []
            for puesto in puestos:
                permisos = []
                nombre_rol = puesto.nombrerol.lower()
                
                if 'vendedor' in nombre_rol or 'registrar venta' in nombre_rol:
                    permisos.extend(['registrar_venta', 'caja'])
                elif 'caja' in nombre_rol or 'cajero' in nombre_rol:
                    permisos.append('caja')
                
                if 'stock' in nombre_rol or 'inventario' in nombre_rol:
                    permisos.append('stock')
                if 'recursos humanos' in nombre_rol or 'rrhh' in nombre_rol:
                    permisos.extend(['crear_empleado', 'asistencias'])
                if 'supervisor' in nombre_rol:
                    permisos.append('asistencias')
                
                salario = 0
                if puesto.descripcionrol and 'Salario: $' in puesto.descripcionrol:
                    try:
                        salario_str = puesto.descripcionrol.split('Salario: $')[1]
                        if '|' in salario_str:
                            salario_str = salario_str.split('|')[0].strip()
                        else:
                            salario_str = salario_str.strip()
                        salario_str = salario_str.replace(',', '').replace(' ', '')
                        salario = float(salario_str)
                    except (ValueError, IndexError, AttributeError) as e:
                        print(f"Error extrayendo salario para {puesto.nombrerol}: {e}")
                        salario = 0
                
                puestos_data.append({
                    'id': puesto.idroles,
                    'nombre': puesto.nombrerol,
                    'permisos': list(set(permisos)),
                    'salario': salario
                })
            
            resultado.append({
                'id': area_nombre,
                'nombre': area_nombre,
                'puestos': puestos_data
            })
        
        return JsonResponse(resultado, safe=False)
    except Exception as e:
        print(f"Error en api_areas_puestos: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@transaction.atomic
def api_crear_area(request):
    """Crea una nueva área creando un rol placeholder."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre_area = data.get('nombre', '').strip()
            
            if not nombre_area:
                return JsonResponse({'error': 'El nombre del área es obligatorio.'}, status=400)
            
            if Roles.objects.filter(nombrearea__iexact=nombre_area).exists():
                return JsonResponse({'error': 'Ya existe un área con este nombre.'}, status=400)
            
            rol_placeholder = Roles.objects.create(
                nombrerol=f"_placeholder_{nombre_area}",
                nombrearea=nombre_area,
                descripcionrol=f"Rol placeholder para el área {nombre_area}. No asignar a usuarios."
            )
            
            return JsonResponse({
                'id': nombre_area,
                'nombre': nombre_area,
                'message': 'Área creada correctamente. Ahora puedes añadir puestos.'
            }, status=201)
            
        except Exception as e:
            print(f"Error en api_crear_area: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@transaction.atomic
def api_editar_area(request, area_nombre):
    """Edita el nombre de un área."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nuevo_nombre = data.get('nombre', '').strip()
            
            if not nuevo_nombre:
                return JsonResponse({'error': 'El nombre del área es obligatorio.'}, status=400)
            
            if not Roles.objects.filter(nombrearea=area_nombre).exists():
                return JsonResponse({'error': 'El área no existe.'}, status=404)
            
            if nuevo_nombre != area_nombre and Roles.objects.filter(nombrearea__iexact=nuevo_nombre).exists():
                return JsonResponse({'error': 'Ya existe un área con este nombre.'}, status=400)
            
            Roles.objects.filter(nombrearea=area_nombre).update(nombrearea=nuevo_nombre)
            
            return JsonResponse({
                'id': nuevo_nombre,
                'nombre': nuevo_nombre,
                'message': 'Área actualizada correctamente.'
            })
            
        except Exception as e:
            print(f"Error en api_editar_area: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@transaction.atomic
def api_crear_puesto_nuevo(request):
    """Crea un nuevo puesto con permisos y salario."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre_puesto = data.get('nombre', '').strip()
            area_id = data.get('area_id')
            permisos = data.get('permisos', [])
            salario = data.get('salario', 0)
            
            if not all([nombre_puesto, area_id]):
                return JsonResponse({'error': 'Faltan datos obligatorios.'}, status=400)
            
            try:
                salario = float(salario)
                if salario < 0:
                    return JsonResponse({'error': 'El salario no puede ser negativo.'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'El salario debe ser un número válido.'}, status=400)
            
            if Roles.objects.filter(
                nombrerol__iexact=nombre_puesto, 
                nombrearea=area_id
            ).exclude(
                nombrerol__startswith='_placeholder_'
            ).exists():
                return JsonResponse({'error': 'Ya existe un puesto con este nombre en esta área.'}, status=400)
            
            Roles.objects.filter(
                nombrearea=area_id,
                nombrerol__startswith='_placeholder_'
            ).delete()
            
            permisos_desc = ', '.join([p.replace('_', ' ').title() for p in permisos]) if permisos else 'Sin permisos'
            descripcion = f'Puesto de {nombre_puesto} con permisos: {permisos_desc} | Salario: ${salario}'
            
            nuevo_puesto = Roles.objects.create(
                nombrerol=nombre_puesto,
                nombrearea=area_id,
                descripcionrol=descripcion
            )
            
            return JsonResponse({
                'id': nuevo_puesto.idroles,
                'nombre': nuevo_puesto.nombrerol,
                'permisos': permisos,
                'salario': salario,
                'message': 'Puesto creado correctamente.'
            }, status=201)
            
        except Exception as e:
            print(f"Error en api_crear_puesto_nuevo: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@transaction.atomic
def api_editar_puesto(request, puesto_id):
    """Edita un puesto existente."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre_puesto = data.get('nombre', '').strip()
            permisos = data.get('permisos', [])
            salario = data.get('salario', 0)
            
            if not nombre_puesto:
                return JsonResponse({'error': 'El nombre del puesto es obligatorio.'}, status=400)
            
            try:
                salario = float(salario)
                if salario < 0:
                    return JsonResponse({'error': 'El salario no puede ser negativo.'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'El salario debe ser un número válido.'}, status=400)
            
            try:
                puesto = Roles.objects.get(idroles=puesto_id)
            except Roles.DoesNotExist:
                return JsonResponse({'error': 'El puesto no existe.'}, status=404)
            
            if Roles.objects.filter(
                nombrerol__iexact=nombre_puesto,
                nombrearea=puesto.nombrearea
            ).exclude(idroles=puesto_id).exists():
                return JsonResponse({'error': 'Ya existe un puesto con este nombre en esta área.'}, status=400)
            
            permisos_desc = ', '.join([p.replace('_', ' ').title() for p in permisos]) if permisos else 'Sin permisos'
            puesto.nombrerol = nombre_puesto
            puesto.descripcionrol = f'Puesto de {nombre_puesto} con permisos: {permisos_desc} | Salario: ${salario}'
            puesto.save()
            
            empleados_actualizados = Empleados.objects.filter(cargoempleado=puesto.nombrerol).update(
                salarioempleado=salario
            )
            
            return JsonResponse({
                'id': puesto.idroles,
                'nombre': puesto.nombrerol,
                'permisos': permisos,
                'salario': salario,
                'empleados_actualizados': empleados_actualizados,
                'message': f'Puesto actualizado correctamente. {empleados_actualizados} empleado(s) actualizado(s).'
            })
            
        except Exception as e:
            print(f"Error en api_editar_puesto: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def api_puestos_por_area_con_permisos(request, area_id):
    """Devuelve todos los puestos de un área con sus permisos y salario."""
    try:
        puestos = Roles.objects.filter(nombrearea=area_id).order_by('nombrerol')
        
        data = []
        for puesto in puestos:
            permisos = []
            nombre_rol = puesto.nombrerol.lower()
            
            if 'vendedor' in nombre_rol or 'registrar venta' in nombre_rol:
                permisos.extend(['registrar_venta', 'caja'])
            elif 'caja' in nombre_rol or 'cajero' in nombre_rol:
                permisos.append('caja')
            
            if 'stock' in nombre_rol or 'inventario' in nombre_rol:
                permisos.append('stock')
            if 'recursos humanos' in nombre_rol or 'rrhh' in nombre_rol:
                permisos.extend(['crear_empleado', 'asistencias'])
            if 'supervisor' in nombre_rol:
                permisos.append('asistencias')
            
            salario = 0
            if puesto.descripcionrol and 'Salario: $' in puesto.descripcionrol:
                try:
                    salario_str = puesto.descripcionrol.split('Salario: $')[1].split('|')[0].strip()
                    salario = float(salario_str.replace(',', ''))
                except:
                    salario = 0
            
            data.append({
                'id': puesto.idroles,
                'nombre': puesto.nombrerol,
                'permisos': list(set(permisos)),
                'salario': salario
            })
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@transaction.atomic
def api_registrar_empleado_actualizado(request):
    """Registra un nuevo empleado con permisos basados en su puesto."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        personal_data = data.get('personal', {})
        
        if personal_data is None:
            return JsonResponse({'error': 'No se recibieron los datos personales.'}, status=400)

        nombre = personal_data.get('nombre', '').strip()
        apellido = personal_data.get('apellido', '').strip()
        email = personal_data.get('email', '').strip()
        dni = personal_data.get('dni')
        foto_base64 = personal_data.get('foto')

        if not all([nombre, apellido, email, dni]):
            return JsonResponse({'error': 'Faltan datos personales obligatorios.'}, status=400)

        if Usuarios.objects.filter(emailusuario__iexact=email).exists():
            return JsonResponse({'error': 'El correo electrónico ya está en uso.'}, status=400)
        
        if Usuarios.objects.filter(dniusuario=dni).exists():
            return JsonResponse({'error': 'El DNI ya está registrado.'}, status=400)

        username = (nombre.split(' ')[0] + apellido.replace(' ', '')).lower()
        temp_username = username
        counter = 1
        while Usuarios.objects.filter(nombreusuario=temp_username).exists():
            temp_username = f"{username}{counter}"
            counter += 1
        username = temp_username
        
        password = ''.join(random.choices(string.digits, k=5))

        nuevo_usuario = Usuarios.objects.create(
            nombreusuario=username,
            apellidousuario=apellido,
            emailusuario=email,
            passwordusuario=password,
            dniusuario=dni,
            telefono=personal_data.get('telefono') or '',
            fecharegistrousuario=timezone.now().date(),
            imagenusuario=foto_base64
        )

        puesto_seleccionado = data.get('puesto', {}) or {}
        puesto_id = puesto_seleccionado.get('id')
        
        salario_puesto = 0
        if puesto_id:
            try:
                rol_puesto = Roles.objects.get(idroles=puesto_id)
                if rol_puesto.descripcionrol and 'Salario: $' in rol_puesto.descripcionrol:
                    try:
                        salario_str = rol_puesto.descripcionrol.split('Salario: $')[1].split('|')[0].strip()
                        salario_puesto = float(salario_str.replace(',', ''))
                    except:
                        salario_puesto = 0
            except Roles.DoesNotExist:
                pass
        
        nuevo_empleado = Empleados.objects.create(
            idusuarios=nuevo_usuario,
            cargoempleado=puesto_seleccionado.get('nombre', 'Sin Puesto'),
            salarioempleado=salario_puesto,
            fechacontratado=timezone.now().date(),
            estado='Trabajando'
        )

        if puesto_id:
            rol_puesto = Roles.objects.get(idroles=puesto_id)
            UsuxRoles.objects.create(idusuarios=nuevo_usuario, idroles=rol_puesto)
            
            horario_data = data.get('horario', {})
            if horario_data:
                dias_semana_map = {'Lu': 0, 'Ma': 1, 'Mi': 2, 'Ju': 3, 'Vi': 4, 'Sa': 5, 'Do': 6}
                day_color_map = horario_data.get('dayColorMap', {})
                schedule_data = horario_data.get('scheduleData', {})
                week_id_map = {}
                current_week_number = 1
                sorted_week_ids = sorted(day_color_map.keys(), key=lambda k: int(k.split('-')[0][1:]) if '-' in k else 0)
                
                for key in sorted_week_ids:
                    week_id = key.split('-')[0] if '-' in key else 'w0'
                    if week_id not in week_id_map:
                        week_id_map[week_id] = current_week_number
                        current_week_number += 1

                for composite_key, color in day_color_map.items():
                    parts = composite_key.split('-')
                    if len(parts) == 2:
                        week_id_str, day_key = parts
                        week_number = week_id_map.get(week_id_str, 1)
                    else:
                        day_key = parts[0]
                        week_number = 1
                    
                    day = dias_semana_map.get(day_key)

                    if day is not None:
                        tramos = schedule_data.get(color, [])
                        for tramo in tramos:
                            if tramo.get('start') and tramo.get('end'):
                                Horario.objects.create(
                                    empleado=nuevo_empleado,
                                    rol=rol_puesto,
                                    dia_semana=day,
                                    semana_del_mes=week_number,
                                    hora_inicio=tramo['start'],
                                    hora_fin=tramo['end']
                                )

        try:
            registrar_actividad(
                request,
                'CREAR_EMPLEADO',
                f'Creación de empleado: {nombre} {apellido}',
                detalles={
                    'empleado_id': nuevo_empleado.idempleado,
                    'puesto': puesto_seleccionado.get('nombre')
                }
            )
            send_mail(
                subject='¡Bienvenido! Tus credenciales de acceso',
                message=f"Hola {nombre},\n\n¡Te damos la bienvenida al sistema! A continuación encontrarás tus datos para iniciar sesión:\n\nNombre de Usuario: {username}\nContraseña Temporal: {password}\n\nTe recomendamos cambiar tu contraseña después de tu primer inicio de sesión.\n\nSaludos,\nEl equipo de La Merced.",
                from_email=None,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error al enviar email: {e}")

        return JsonResponse({
            'message': f'¡Empleado {nombre} {apellido} creado exitosamente!',
            'username': username,
            'salario': salario_puesto
        }, status=201)

    except Exception as e:
        return JsonResponse({'error': f'Ocurrió un error inesperado: {str(e)}'}, status=500)


def lista_empleados_view(request: HttpRequest) -> HttpResponse:
    """Vista para la lista de empleados."""
    if not _verificar_autenticacion(request):
        messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
        return redirect('login')
    
    usuario_id = request.session.get('usuario_id')
    usuario = Usuarios.objects.filter(idusuarios=usuario_id).first()
    
    if not usuario:
        messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
        return redirect('login')
    
    roles_usuario = list(
        Roles.objects.filter(usuxroles__idusuarios_id=usuario_id).values_list('nombrerol', flat=True)
    )
    
    is_admin = 'Administrador' in roles_usuario or 'Recursos Humanos' in roles_usuario
    
    if not is_admin:
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('inicio')
    
    return render(request, 'HTML/lista_empleados.html')


def gestion_stock_view(request: HttpRequest) -> HttpResponse:
    """Vista para gestión de stock."""
    if not _verificar_autenticacion(request):
        messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
        return redirect('login')
    
    es_valido, mensaje_error = _verificar_estado_empleado(request)
    if not es_valido:
        request.session.flush()
        messages.error(request, mensaje_error)
        return redirect('login')
    
    usuario_id = request.session.get('usuario_id')
    usuario = Usuarios.objects.filter(idusuarios=usuario_id).first()
    
    if not usuario:
        messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
        return redirect('login')
    
    roles_usuario = list(
        Roles.objects.filter(usuxroles__idusuarios_id=usuario_id).values_list('nombrerol', flat=True)
    )
    
    is_admin = 'Administrador' in roles_usuario or 'Recursos Humanos' in roles_usuario
    has_gestion_stock = 'Gestor de Inventario' in roles_usuario or 'Gestión de Stock' in roles_usuario or 'Stock' in roles_usuario
    
    if not (is_admin or has_gestion_stock):
        messages.error(request, 'No tienes permisos para acceder a Gestión de Stock.')
        return redirect('inicio')
    
    try:
        return render(request, 'GestionDeStock/index.html')
    except:
        try:
            return render(request, 'index.html')
        except:
            return render(request, 'HTML/gestion_stock.html', {
                'mensaje': 'Gestión de Stock - En desarrollo'
            })


def menu_caja_view(request: HttpRequest) -> HttpResponse:
    """Vista para el menú de caja."""
    if not _verificar_autenticacion(request):
        messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
        return redirect('login')
    
    es_valido, mensaje_error = _verificar_estado_empleado(request)
    if not es_valido:
        request.session.flush()
        messages.error(request, mensaje_error)
        return redirect('login')
    
    usuario_id = request.session.get('usuario_id')
    usuario = Usuarios.objects.filter(idusuarios=usuario_id).first()
    
    if not usuario:
        messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
        return redirect('login')
    
    roles_usuario = list(
        Roles.objects.filter(usuxroles__idusuarios_id=usuario_id).values_list('nombrerol', flat=True)
    )
    
    is_admin = 'Administrador' in roles_usuario or 'Recursos Humanos' in roles_usuario
    has_registrar_venta = 'Vendedor' in roles_usuario or 'Registrar Venta' in roles_usuario
    has_caja = has_registrar_venta or 'Supervisor de Caja' in roles_usuario or 'Caja' in roles_usuario
    
    if not (is_admin or has_caja):
        messages.error(request, 'No tienes permisos para acceder a Caja.')
        return redirect('inicio')
    
    try:
        return render(request, 'caja/menucaja.html')
    except:
        try:
            return render(request, 'menucaja.html')
        except:
            return render(request, 'aperturadecaja.html')


def gestion_areas_puestos_view(request: HttpRequest) -> HttpResponse:
    """Vista para gestionar áreas y puestos (solo administradores)."""
    if not _verificar_autenticacion(request):
        messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
        return redirect('login')
    
    es_valido, mensaje_error = _verificar_estado_empleado(request)
    if not es_valido:
        request.session.flush()
        messages.error(request, mensaje_error)
        return redirect('login')
    
    usuario_id = request.session.get('usuario_id')
    usuario = Usuarios.objects.filter(idusuarios=usuario_id).first()
    
    if not usuario:
        messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
        return redirect('login')
    
    roles_usuario = list(
        Roles.objects.filter(usuxroles__idusuarios_id=usuario_id).values_list('nombrerol', flat=True)
    )
    
    is_admin = 'Administrador' in roles_usuario or 'Recursos Humanos' in roles_usuario
    
    if not is_admin:
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('inicio')
    
    return render(request, 'HTML/gestion_areas_puestos.html')


def _generar_y_enviar_codigo(request: HttpRequest, destino: str) -> None:
    """Genera un código de 5 dígitos y lo envía por email."""
    codigo = f"{random.randint(0, 99999):05d}"
    expira = timezone.now() + timedelta(minutes=CODIGO_EXPIRA_MINUTOS)
    request.session['codigo_estado'] = {'codigo': codigo, 'expira': expira.isoformat()}
    
    try:
        send_mail(
            subject='Código de recuperación',
            message=f'Tu código es {codigo}. Caduca en {CODIGO_EXPIRA_MINUTOS} minutos.',
            from_email=None,
            recipient_list=[destino],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error al enviar email: {e}")


@require_http_methods(['GET'])
def api_lista_empleados(request: HttpRequest) -> JsonResponse:
    """API para obtener la lista de empleados (optimizada para grandes cantidades)."""
    try:
        empleados = Empleados.objects.select_related(
            'idusuarios'
        ).prefetch_related(
            'idusuarios__roles'
        ).values(
            'idempleado',
            'idusuarios__nombreusuario',
            'idusuarios__apellidousuario',
            'idusuarios__dniusuario',
            'idusuarios__emailusuario',
            'idusuarios__telefono',
            'idusuarios__imagenusuario',
            'cargoempleado',
            'estado',
            'fechacontratado'
        ).order_by('-fechacontratado')
        
        empleados_list = []
        for emp in empleados:
            usuario_id = Empleados.objects.get(idempleado=emp['idempleado']).idusuarios_id
            roles = Roles.objects.filter(usuxroles__idusuarios_id=usuario_id).first()
            
            empleados_list.append({
                'id': emp['idempleado'],
                'nombre': emp['idusuarios__nombreusuario'],
                'apellido': emp['idusuarios__apellidousuario'],
                'dni': emp['idusuarios__dniusuario'],
                'email': emp['idusuarios__emailusuario'],
                'telefono': emp['idusuarios__telefono'] or '',
                'imagen': emp['idusuarios__imagenusuario'],
                'puesto': emp['cargoempleado'],
                'area': roles.nombrearea if roles else 'Sin área',
                'estado': emp['estado'],
                'fecha_contratado': emp['fechacontratado'].isoformat() if emp['fechacontratado'] else None
            })
        
        return JsonResponse({
            'empleados': empleados_list
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['GET'])
def api_detalle_empleado(request: HttpRequest, empleado_id: int) -> JsonResponse:
    """API para obtener el detalle completo de un empleado."""
    try:
        empleado = Empleados.objects.select_related('idusuarios').get(idempleado=empleado_id)
        usuario = empleado.idusuarios
        
        rol = Roles.objects.filter(usuxroles__idusuarios=usuario).first()
        
        horarios = Horario.objects.filter(empleado=empleado).values(
            'dia_semana',
            'semana_del_mes',
            'hora_inicio',
            'hora_fin'
        ).order_by('semana_del_mes', 'dia_semana')
        
        data = {
            'id': empleado.idempleado,
            'nombre': usuario.nombreusuario,
            'apellido': usuario.apellidousuario,
            'dni': usuario.dniusuario,
            'email': usuario.emailusuario,
            'telefono': usuario.telefono or '',
            'imagen': usuario.imagenusuario,
            'direccion': getattr(usuario, 'direccion', '') or '',
            'fecha_nacimiento': str(getattr(usuario, 'fecha_nacimiento', '')) if getattr(usuario, 'fecha_nacimiento', None) else '',
            'puesto': empleado.cargoempleado,
            'area': rol.nombrearea if rol else 'Sin área',
            'area_id': rol.nombrearea if rol else None,
            'puesto_id': rol.idroles if rol else None,
            'salario': float(empleado.salarioempleado),
            'estado': empleado.estado,
            'fecha_contratado': empleado.fechacontratado.isoformat() if empleado.fechacontratado else None,
            'fecha_registro': usuario.fecharegistrousuario.isoformat() if usuario.fecharegistrousuario else None,
            'usuario': usuario.nombreusuario,
            'horarios': [
                {
                    'dia_semana': h['dia_semana'],
                    'semana_del_mes': h['semana_del_mes'],
                    'hora_inicio': h['hora_inicio'].strftime('%H:%M') if h['hora_inicio'] else '',
                    'hora_fin': h['hora_fin'].strftime('%H:%M') if h['hora_fin'] else ''
                }
                for h in horarios
            ]
        }
        
        return JsonResponse(data)
        
    except Empleados.DoesNotExist:
        return JsonResponse({'error': 'Empleado no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
@transaction.atomic
def api_editar_empleado(request: HttpRequest, empleado_id: int) -> JsonResponse:
    """API para editar un empleado."""
    try:
        data = json.loads(request.body)
        
        nombre = data.get('nombre', '').strip()
        apellido = data.get('apellido', '').strip()
        dni = data.get('dni', '').strip()
        email = data.get('email', '').strip()
        
        if not all([nombre, apellido, dni, email]):
            return JsonResponse({'error': 'Faltan datos obligatorios'}, status=400)
        
        empleado = Empleados.objects.select_related('idusuarios').get(idempleado=empleado_id)
        usuario = empleado.idusuarios
        
        if Usuarios.objects.filter(emailusuario=email).exclude(idusuarios=usuario.idusuarios).exists():
            return JsonResponse({'error': 'El email ya está en uso por otro empleado'}, status=400)
        
        if Usuarios.objects.filter(dniusuario=dni).exclude(idusuarios=usuario.idusuarios).exists():
            return JsonResponse({'error': 'El DNI ya está registrado por otro empleado'}, status=400)
        
        usuario.nombreusuario = nombre
        usuario.apellidousuario = apellido
        usuario.dniusuario = dni
        usuario.emailusuario = email
        usuario.telefono = data.get('telefono', '')
        usuario.save()
        
        empleado.salarioempleado = float(data.get('salario', 0))
        estado_anterior = empleado.estado
        empleado.estado = data.get('estado', 'Trabajando')
        
        puesto_id = data.get('puesto_id')
        if puesto_id:
            try:
                nuevo_rol = Roles.objects.get(idroles=puesto_id)
                empleado.cargoempleado = nuevo_rol.nombrerol
                
                UsuxRoles.objects.filter(idusuarios=usuario).delete()
                UsuxRoles.objects.create(idusuarios=usuario, idroles=nuevo_rol)
                
            except Roles.DoesNotExist:
                return JsonResponse({'error': 'El puesto seleccionado no existe'}, status=400)
        
        empleado.save()
        
        horarios_data = data.get('horarios', [])
        if horarios_data is not None:
            Horario.objects.filter(empleado=empleado).delete()
            
            if horarios_data:
                rol_actual = Roles.objects.filter(usuxroles__idusuarios=usuario).first()
                for horario in horarios_data:
                    Horario.objects.create(
                        empleado=empleado,
                        rol=rol_actual,
                        dia_semana=horario.get('dia_semana'),
                        semana_del_mes=horario.get('semana_del_mes'),
                        hora_inicio=horario.get('hora_inicio'),
                        hora_fin=horario.get('hora_fin')
                    )
        
        return JsonResponse({
            'message': 'Empleado actualizado correctamente',
            'empleado': {
                'id': empleado.idempleado,
                'nombre': usuario.nombreusuario,
                'apellido': usuario.apellidousuario,
                'email': usuario.emailusuario,
                'estado': empleado.estado
            }
        })
        
    except Empleados.DoesNotExist:
        return JsonResponse({'error': 'Empleado no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Error al actualizar: {str(e)}'}, status=500)


@require_http_methods(['GET'])
def api_areas_simple(request: HttpRequest) -> JsonResponse:
    """API para obtener lista simple de áreas."""
    try:
        areas = Roles.objects.values('nombrearea').distinct().order_by('nombrearea')
        
        areas_list = []
        for idx, area in enumerate(areas, start=1):
            primer_rol = Roles.objects.filter(nombrearea=area['nombrearea']).first()
            areas_list.append({
                'id': area['nombrearea'],
                'nombre': area['nombrearea']
            })
        
        return JsonResponse(areas_list, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['GET'])
def api_puestos_por_area_simple(request: HttpRequest, area_nombre: str) -> JsonResponse:
    """API para obtener puestos de un área específica (para el select de edición)."""
    try:
        puestos = Roles.objects.filter(nombrearea=area_nombre).order_by('nombrerol')
        
        puestos_list = [
            {
                'id': puesto.idroles,
                'nombre': puesto.nombrerol
            }
            for puesto in puestos
        ]
        
        return JsonResponse(puestos_list, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
from django.core.paginator import Paginator
import json
from .utils import registrar_actividad, leer_logs, obtener_estadisticas_logs

@require_http_methods(['GET'])
def logs_actividad_view(request):
    """Vista principal de logs de actividad - SOLO ADMINISTRADORES"""
    if not _verificar_autenticacion(request):
        messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
        return redirect('login')
    
    usuario_id = request.session.get('usuario_id')
    
    # Verificar que sea administrador
    roles_usuario = list(
        Roles.objects.filter(usuxroles__idusuarios_id=usuario_id).values_list('nombrerol', flat=True)
    )
    
    is_admin = 'Administrador' in roles_usuario or 'Recursos Humanos' in roles_usuario
    
    if not is_admin:
        messages.error(request, 'No tienes permisos para acceder a los logs de actividad.')
        return redirect('inicio')
    
    return render(request, 'HTML/logs_actividad.html', {
        'usuario_nombre': request.session.get('nombre_usuario', 'Usuario')
    })

@require_http_methods(['GET'])
def api_logs_actividad(request):
    """API para obtener logs de actividad con filtros"""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    # Verificar permisos de administrador
    roles_usuario = list(
        Roles.objects.filter(usuxroles__idusuarios_id=usuario_id).values_list('nombrerol', flat=True)
    )
    
    if not ('Administrador' in roles_usuario or 'Recursos Humanos' in roles_usuario):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    try:
        # Parámetros de filtrado
        search = request.GET.get('search', '').strip()
        tipo = request.GET.get('tipo', 'all')
        nivel = request.GET.get('nivel', 'all')
        fecha_inicio = request.GET.get('fecha_inicio', '')
        fecha_fin = request.GET.get('fecha_fin', '')
        page = int(request.GET.get('page', 1))
        
        # Leer logs con filtros
        logs = leer_logs(
            fecha_inicio=fecha_inicio if fecha_inicio else None,
            fecha_fin=fecha_fin if fecha_fin else None,
            tipo=tipo if tipo != 'all' else None,
            nivel=nivel if nivel != 'all' else None,
            search=search if search else None,
            limit=10000  # Límite alto para paginación
        )
        
        # Paginación manual
        paginator = Paginator(logs, 50)
        page_obj = paginator.get_page(page)
        
        # Agregar ID único a cada log (basado en timestamp)
        logs_data = []
        for idx, log in enumerate(page_obj):
            log_copy = log.copy()
            log_copy['id'] = hash(log.get('timestamp', str(idx)))
            log_copy['tipo_actividad_display'] = get_tipo_display_name(log.get('tipo_actividad', ''))
            log_copy['nivel_display'] = get_nivel_display_name(log.get('nivel', 'INFO'))
            logs_data.append(log_copy)
        
        return JsonResponse({
            'logs': logs_data,
            'total': paginator.count,
            'page': page,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(['GET'])
def api_estadisticas_logs(request):
    """API para obtener estadísticas de los logs"""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    # Verificar permisos
    roles_usuario = list(
        Roles.objects.filter(usuxroles__idusuarios_id=usuario_id).values_list('nombrerol', flat=True)
    )
    
    if not ('Administrador' in roles_usuario or 'Recursos Humanos' in roles_usuario):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    try:
        estadisticas = obtener_estadisticas_logs(dias=7)
        return JsonResponse(estadisticas)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(['GET'])
def api_detalle_log(request, log_timestamp):
    """API para obtener el detalle completo de un log por timestamp"""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    # Verificar permisos
    roles_usuario = list(
        Roles.objects.filter(usuxroles__idusuarios_id=usuario_id).values_list('nombrerol', flat=True)
    )
    
    if not ('Administrador' in roles_usuario or 'Recursos Humanos' in roles_usuario):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    try:
        # Leer todos los logs y buscar por timestamp
        logs = leer_logs(limit=100000)
        
        log = None
        for l in logs:
            if l.get('timestamp') == log_timestamp:
                log = l
                break
        
        if not log:
            return JsonResponse({'error': 'Log no encontrado'}, status=404)
        
        log['id'] = hash(log.get('timestamp', ''))
        log['tipo_actividad_display'] = get_tipo_display_name(log.get('tipo_actividad', ''))
        log['nivel_display'] = get_nivel_display_name(log.get('nivel', 'INFO'))
        
        return JsonResponse(log)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_tipo_display_name(tipo):
    """Convierte el tipo de actividad a nombre legible"""
    nombres = {
        'LOGIN': 'Inicio de Sesión',
        'LOGOUT': 'Cierre de Sesión',
        'ENTRADA': 'Registro de Entrada',
        'SALIDA': 'Registro de Salida',
        'APERTURA_CAJA': 'Apertura de Caja',
        'CIERRE_CAJA': 'Cierre de Caja',
        'VENTA': 'Venta Realizada',
        'CREAR_EMPLEADO': 'Creación de Empleado',
        'EDITAR_EMPLEADO': 'Edición de Empleado',
        'CREAR_AREA': 'Creación de Área',
        'EDITAR_AREA': 'Edición de Área',
        'CREAR_PUESTO': 'Creación de Puesto',
        'EDITAR_PUESTO': 'Edición de Puesto',
        'CREAR_PRODUCTO': 'Creación de Producto',
        'EDITAR_PRODUCTO': 'Edición de Producto',
        'ELIMINAR_PRODUCTO': 'Eliminación de Producto',
        'CAMBIO_ESTADO': 'Cambio de Estado de Empleado',
    }
    return nombres.get(tipo, tipo)

def get_nivel_display_name(nivel):
    """Convierte el nivel a nombre legible"""
    nombres = {
        'INFO': 'Información',
        'WARNING': 'Advertencia',
        'ERROR': 'Error',
        'CRITICAL': 'Crítico',
    }
    return nombres.get(nivel, nivel)

# Agregar estos nuevos endpoints al archivo views.py

@require_http_methods(['GET'])
def api_buscar_empleados(request: HttpRequest) -> JsonResponse:
    """API para buscar empleados existentes por nombre, apellido o DNI."""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse([], safe=False)
    
    try:
        # Buscar por nombre, apellido o DNI
        empleados = Empleados.objects.select_related('idusuarios').filter(
            Q(idusuarios__nombreusuario__icontains=query) |
            Q(idusuarios__apellidousuario__icontains=query) |
            Q(idusuarios__dniusuario__icontains=query)
        ).order_by('idusuarios__nombreusuario')[:10]
        
        resultado = []
        for emp in empleados:
            usuario = emp.idusuarios
            
            # Obtener todos los roles actuales del empleado
            roles_actuales = list(
                Roles.objects.filter(usuxroles__idusuarios=usuario).values(
                    'idroles', 'nombrerol', 'nombrearea'
                )
            )
            
            resultado.append({
                'id': emp.idempleado,
                'usuario_id': usuario.idusuarios,
                'nombre': usuario.nombreusuario,
                'apellido': usuario.apellidousuario,
                'dni': usuario.dniusuario,
                'email': usuario.emailusuario,
                'telefono': usuario.telefono or '',
                'imagen': usuario.imagenusuario,
                'roles_actuales': roles_actuales,
                'estado': emp.estado
            })
        
        return JsonResponse(resultado, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['GET'])
def api_roles_empleado(request: HttpRequest, empleado_id: int) -> JsonResponse:
    """API para obtener todos los roles de un empleado."""
    try:
        empleado = Empleados.objects.select_related('idusuarios').get(idempleado=empleado_id)
        usuario = empleado.idusuarios
        
        roles = Roles.objects.filter(usuxroles__idusuarios=usuario).values(
            'idroles', 'nombrerol', 'nombrearea', 'descripcionrol'
        )
        
        return JsonResponse({
            'empleado_id': empleado.idempleado,
            'nombre_completo': f"{usuario.nombreusuario} {usuario.apellidousuario}",
            'roles': list(roles)
        })
        
    except Empleados.DoesNotExist:
        return JsonResponse({'error': 'Empleado no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
@transaction.atomic
def api_asignar_nuevo_rol(request: HttpRequest) -> JsonResponse:
    """API para asignar un nuevo rol/área a un empleado existente."""
    try:
        data = json.loads(request.body)
        
        empleado_id = data.get('empleado_id')
        puesto_id = data.get('puesto_id')
        horario_data = data.get('horario', {})
        
        if not empleado_id or not puesto_id:
            return JsonResponse({'error': 'Faltan datos obligatorios'}, status=400)
        
        # Verificar que el empleado existe
        empleado = Empleados.objects.select_related('idusuarios').get(idempleado=empleado_id)
        usuario = empleado.idusuarios
        
        # Verificar que el puesto existe
        nuevo_rol = Roles.objects.get(idroles=puesto_id)
        
        # Verificar que el empleado no tenga ya este rol asignado
        if UsuxRoles.objects.filter(idusuarios=usuario, idroles=nuevo_rol).exists():
            return JsonResponse({
                'error': f'El empleado ya tiene asignado el puesto "{nuevo_rol.nombrerol}"'
            }, status=400)
        
        # Asignar el nuevo rol
        UsuxRoles.objects.create(idusuarios=usuario, idroles=nuevo_rol)
        
        # Procesar horarios si se proporcionaron
        if horario_data:
            dias_semana_map = {'Lu': 0, 'Ma': 1, 'Mi': 2, 'Ju': 3, 'Vi': 4, 'Sa': 5, 'Do': 6}
            day_color_map = horario_data.get('dayColorMap', {})
            schedule_data = horario_data.get('scheduleData', {})
            
            # Mapeo de semanas
            week_id_map = {}
            current_week_number = 1
            sorted_week_ids = sorted(
                day_color_map.keys(), 
                key=lambda k: int(k.split('-')[0][1:]) if '-' in k else 0
            )
            
            for key in sorted_week_ids:
                week_id = key.split('-')[0] if '-' in key else 'w0'
                if week_id not in week_id_map:
                    week_id_map[week_id] = current_week_number
                    current_week_number += 1
            
            # Crear horarios
            for composite_key, color in day_color_map.items():
                parts = composite_key.split('-')
                if len(parts) == 2:
                    week_id_str, day_key = parts
                    week_number = week_id_map.get(week_id_str, 1)
                else:
                    day_key = parts[0]
                    week_number = 1
                
                day = dias_semana_map.get(day_key)
                
                if day is not None:
                    tramos = schedule_data.get(color, [])
                    for tramo in tramos:
                        if tramo.get('start') and tramo.get('end'):
                            Horario.objects.create(
                                empleado=empleado,
                                rol=nuevo_rol,
                                dia_semana=day,
                                semana_del_mes=week_number,
                                hora_inicio=tramo['start'],
                                hora_fin=tramo['end']
                            )
        
        # Registrar actividad
        registrar_actividad(
            request,
            'ASIGNAR_ROL',
            f'Se asignó el rol "{nuevo_rol.nombrerol}" al empleado {usuario.nombreusuario} {usuario.apellidousuario}',
            detalles={
                'empleado_id': empleado.idempleado,
                'rol_id': nuevo_rol.idroles,
                'rol_nombre': nuevo_rol.nombrerol,
                'area': nuevo_rol.nombrearea
            }
        )
        
        return JsonResponse({
            'message': f'Rol "{nuevo_rol.nombrerol}" asignado correctamente al empleado',
            'empleado': {
                'id': empleado.idempleado,
                'nombre': f"{usuario.nombreusuario} {usuario.apellidousuario}"
            },
            'nuevo_rol': {
                'id': nuevo_rol.idroles,
                'nombre': nuevo_rol.nombrerol,
                'area': nuevo_rol.nombrearea
            }
        }, status=201)
        
    except Empleados.DoesNotExist:
        return JsonResponse({'error': 'Empleado no encontrado'}, status=404)
    except Roles.DoesNotExist:
        return JsonResponse({'error': 'Puesto no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Error al asignar rol: {str(e)}'}, status=500)


# También agregar import al inicio del archivo:
from django.db.models import Q