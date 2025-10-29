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

from caja.models import (
    Usuarios, Roles, UsuxRoles, Empleados, Horario, Caja, Asistencias
)

MAX_INTENTOS = 3
BLOQUEO_MINUTOS = 5
CODIGO_EXPIRA_MINUTOS = 5


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
            horacierrecaja=time(0, 0, 0)
        ).exists()
        return caja_abierta
    except Exception as e:
        print(f"Error verificando caja: {e}")
        return False


def login_view(request: HttpRequest) -> HttpResponse:
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

        # Validar estado del empleado
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

        # Usuario autenticado correctamente
        estado['intentos'] = 0
        estado['bloqueado_hasta'] = None
        request.session['login_estado'] = estado

        request.session['usuario_id'] = usuario.idusuarios
        request.session['nombre_usuario'] = usuario.nombreusuario

        # ✅ REGISTRAR ENTRADA AUTOMÁTICAMENTE
        entrada_registrada = _registrar_entrada_automatica(usuario.idusuarios)
        if entrada_registrada:
            messages.success(request, f'¡Bienvenido! Tu entrada ha sido registrada a las {timezone.localtime().strftime("%H:%M")}.')

        roles_ids = list(UsuxRoles.objects.filter(idusuarios=usuario).values_list('idroles', flat=True))
        if len(roles_ids) <= 1:
            if roles_ids:
                request.session['rol_id'] = roles_ids[0]
            return redirect('inicio')
        else:
            return redirect('seleccionar_rol')

    return render(request, 'HTML/login.html')


def logout_view(request: HttpRequest) -> HttpResponse:
    """
    Cierra la sesión y registra automáticamente la salida.
    Ya NO hay periodo de gracia de 2 minutos.
    """
    usuario_id = request.session.get('usuario_id')
    
    # ✅ REGISTRAR SALIDA AUTOMÁTICAMENTE
    if usuario_id:
        salida_registrada = _registrar_salida_automatica(usuario_id)
        if salida_registrada:
            print(f"✅ Salida registrada automáticamente para usuario ID: {usuario_id}")

    # Cerrar sesión
    try:
        request.session.flush()
    except Exception:
        request.session.clear()

    messages.success(request, 'Tu salida ha sido registrada correctamente. ¡Hasta pronto!')
    return redirect('login')


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
    
    # Validar estado del empleado en tiempo real
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
    
    roles_usuario = Roles.objects.filter(usuxroles__idusuarios_id=usuario_id)
    
    is_admin = any(
        'administrador' in rol.nombrerol.lower() or 
        'recursos humanos' in rol.nombrerol.lower() or
        'rrhh' in rol.nombrerol.lower()
        for rol in roles_usuario
    ) or roles_usuario.count() > 2
    
    permisos_usuario = set()
    
    for rol in roles_usuario:
        nombre_rol_lower = rol.nombrerol.lower()
        descripcion_rol_lower = (rol.descripcionrol or '').lower()
        
        if 'vendedor' in nombre_rol_lower or 'registrar venta' in nombre_rol_lower:
            permisos_usuario.add('registrar_venta')
            permisos_usuario.add('caja')
        
        if 'caja' in nombre_rol_lower or 'cajero' in nombre_rol_lower:
            permisos_usuario.add('caja')
        
        if 'stock' in nombre_rol_lower or 'inventario' in nombre_rol_lower:
            permisos_usuario.add('stock')
        
        if 'supervisor' in nombre_rol_lower:
            permisos_usuario.add('asistencias')
        
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
    
    if is_admin:
        has_caja = True
        has_registrar_venta = True
        has_gestion_stock = True
    else:
        has_caja = 'caja' in permisos_usuario
        has_registrar_venta = 'registrar_venta' in permisos_usuario or 'caja' in permisos_usuario
        has_gestion_stock = 'stock' in permisos_usuario
    
    caja_abierta = _get_caja_abierta(usuario_id)
    
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


# ===== FUNCIONES AUXILIARES PARA OTRAS VISTAS =====

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