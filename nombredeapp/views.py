# ignaciocasula/lamercedcomestiblessuper/LaMercedComestiblesSuper-01f8d833acd495d85802e57720fa43f65e7b42b3/nombredeapp/views.py

from django.shortcuts import render, redirect
from caja.models import Usuarios as Usuario, Empleados as Empleado, Roles as Rol, Usuariosxrol as UsuarioRol, RegistroSeguridad, TokenRecuperacion, Asistencias, Permiso, Herramienta
from django.utils import timezone
from datetime import timedelta, date
import random
import json

def obtener_ip(request):
    """Obtiene la dirección IP real del cliente."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def iniciar_sesion(request):
    """Gestiona el inicio de sesión de los usuarios."""
    if request.method == 'POST':
        intento_usuario = request.POST.get('username')
        intento_contrasena = request.POST.get('password')
        direccion_ip = obtener_ip(request)

        try:
            usuario = Usuario.objects.get(nombreusuario=intento_usuario)
            
            if usuario.passwordusuario == intento_contrasena:
                try:
                    empleado = Empleado.objects.get(idusuarios=usuario)
                    if empleado.estado == 'Trabajando':
                        last_asistencia_id = request.session.get('last_asistencia_id')
                        grace_period_end_str = request.session.get('grace_period_end')
                        
                        if last_asistencia_id and grace_period_end_str:
                            grace_period_end = timezone.datetime.fromisoformat(grace_period_end_str)
                            if timezone.now() <= grace_period_end:
                                try:
                                    asistencia_a_revertir = Asistencias.objects.get(pk=last_asistencia_id, idempleado=empleado)
                                    asistencia_a_revertir.horasalida = None
                                    asistencia_a_revertir.save()
                                except Asistencias.DoesNotExist:
                                    pass
                            
                            del request.session['last_asistencia_id']
                            del request.session['grace_period_end']

                        conteo_roles = UsuarioRol.objects.filter(idusuarios=usuario).count()

                        if conteo_roles > 1:
                            request.session['pre_auth_usuario_id'] = usuario.idusuarios
                            return redirect('seleccionar_rol')
                        else:
                            rol_relacion = UsuarioRol.objects.filter(idusuarios=usuario).first()
                            request.session['usuario_id'] = usuario.idusuarios
                            request.session['nombre_usuario'] = usuario.nombreusuario
                            request.session['apellido_usuario'] = usuario.apellidousuario
                            if rol_relacion:
                                request.session['rol_id'] = rol_relacion.idroles.idroles
                                request.session['rol_nombre'] = rol_relacion.idroles.nombrerol
                            else:
                                request.session['rol_nombre'] = "Sin puesto asignado"
                            return redirect('inicio')
                            
                    else:
                        RegistroSeguridad.objects.create(
                            direccion_ip=direccion_ip, intento_usuario=intento_usuario, intento_contrasena=intento_contrasena,
                            motivo=f'Intento de login de empleado no activo. Estado: {empleado.estado}'
                        )
                        # RUTA CORREGIDA AQUÍ
                        return render(request, 'HTML/login.html', {'error': f'Acceso denegado. Su estado es: {empleado.estado}.'})

                except Empleado.DoesNotExist:
                    RegistroSeguridad.objects.create(
                        direccion_ip=direccion_ip, intento_usuario=intento_usuario, intento_contrasena=intento_contrasena,
                        motivo='Usuario existe pero no es empleado.'
                    )
                    # RUTA CORREGIDA AQUÍ
                    return render(request, 'HTML/login.html', {'error': 'Este usuario no es un empleado válido.'})
            else:
                RegistroSeguridad.objects.create(
                    direccion_ip=direccion_ip, intento_usuario=intento_usuario, intento_contrasena=intento_contrasena,
                    motivo='Contraseña incorrecta.'
                )
                # RUTA CORREGIDA AQUÍ
                return render(request, 'HTML/login.html', {'error': 'Ha ingresado mal la contraseña.'})

        except Usuario.DoesNotExist:
            RegistroSeguridad.objects.create(
                direccion_ip=direccion_ip, intento_usuario=intento_usuario, intento_contrasena=intento_contrasena,
                motivo='El empleado no existe.'
            )
            # RUTA CORREGIDA AQUÍ
            return render(request, 'HTML/login.html', {'error': 'El empleado no existe.'})

    # RUTA CORREGIDA AQUÍ
    return render(request, 'HTML/login.html')

def seleccionar_rol(request):
    """Permite al usuario con múltiples roles elegir con cuál acceder."""
    usuario_id = request.session.get('pre_auth_usuario_id')
    if not usuario_id:
        return redirect('iniciar_sesion')

    usuario = Usuario.objects.get(idusuarios=usuario_id)
    roles_del_usuario = UsuarioRol.objects.filter(idusuarios=usuario).select_related('idroles', 'idroles__area')

    if request.method == 'POST':
        rol_id_seleccionado = request.POST.get('rol_id')
        rol_seleccionado = Rol.objects.get(idroles=rol_id_seleccionado)

        request.session['usuario_id'] = usuario.idusuarios
        request.session['nombre_usuario'] = usuario.nombreusuario
        request.session['apellido_usuario'] = usuario.apellidousuario
        request.session['rol_id'] = rol_seleccionado.idroles
        request.session['rol_nombre'] = rol_seleccionado.nombrerol
        del request.session['pre_auth_usuario_id']
        return redirect('inicio')

    areas_disponibles = sorted(
        list(set(relacion.idroles.area for relacion in roles_del_usuario if relacion.idroles.area)),
        key=lambda area: area.nombrearea
    )
    
    roles_por_area = {}
    for relacion in roles_del_usuario:
        if relacion.idroles.area:
            area_id = relacion.idroles.area.idarea
            if area_id not in roles_por_area:
                roles_por_area[area_id] = []
            roles_por_area[area_id].append({
                'id': relacion.idroles.idroles,
                'nombre': relacion.idroles.nombrerol
            })

    context = {
        'areas': areas_disponibles,
        'roles_por_area_json': json.dumps(roles_por_area)
    }
    return render(request, 'HTML/seleccionar_rol.html')

def pagina_inicio(request):
    """Página principal a la que se accede después de iniciar sesión."""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('iniciar_sesion')
    
    nombre_usuario = request.session.get('nombre_usuario', '').capitalize()
    
    rol_id = request.session.get('rol_id')
    herramientas_permitidas = []
    if rol_id:
        permisos = Permiso.objects.filter(rol_id=rol_id).select_related('herramienta')
        herramientas_permitidas = [p.herramienta for p in permisos]
        
    tiene_permiso_vista_previa = any(h.url_nombre == 'vista_previa' for h in herramientas_permitidas)

    context = {
        'nombre_usuario': nombre_usuario,
        'herramientas': herramientas_permitidas,
        'tiene_permiso_vista_previa': tiene_permiso_vista_previa,
    }
    return render(request, 'HTML/inicio.html', context)


def cerrar_sesion(request):
    """Cierra la sesión del usuario, registra la hora de salida y activa un período de gracia de 10 minutos."""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('iniciar_sesion')

    try:
        empleado = Empleado.objects.get(idusuarios_id=usuario_id)
        asistencia_actual = Asistencias.objects.filter(
            idempleado=empleado, 
            fechaasistencia=date.today(),
            horasalida__isnull=True
        ).order_by('-horaentrada').first()

        if asistencia_actual:
            asistencia_actual.horasalida = timezone.now().time()
            asistencia_actual.save()
            request.session['last_asistencia_id'] = asistencia_actual.idasistencia
            request.session['grace_period_end'] = (timezone.now() + timedelta(minutes=10)).isoformat()

    except Empleado.DoesNotExist:
        pass
    except Exception as e:
        print(f"Error al registrar salida: {e}")

    last_asistencia_id = request.session.get('last_asistencia_id')
    grace_period_end = request.session.get('grace_period_end')
    
    request.session.flush()
    
    if last_asistencia_id and grace_period_end:
        request.session['last_asistencia_id'] = last_asistencia_id
        request.session['grace_period_end'] = grace_period_end
        
    return redirect('iniciar_sesion')

def solicitar_usuario(request):
    """Primer paso para recuperar contraseña: el usuario ingresa su nombre."""
    if request.method == 'POST':
        username = request.POST.get('username_from_login') or request.POST.get('username')
        
        if not username:
            return render(request, 'HTML/solicitar_usuario.html', {'error': 'Debe ingresar un nombre de usuario.'})

        try:
            usuario = Usuario.objects.get(nombreusuario=username)
            empleado = Empleado.objects.get(idusuarios=usuario, estado='Trabajando')

            TokenRecuperacion.objects.filter(usuario=empleado.idusuarios, activo=True).update(activo=False)

            codigo_sms = str(random.randint(10000, 99999))
            expiracion = timezone.now() + timedelta(minutes=5)
            
            TokenRecuperacion.objects.create(
                usuario=empleado.idusuarios,
                codigo_sms=codigo_sms,
                expiracion_codigo_sms=expiracion,
                expiracion_token_email=timezone.now() + timedelta(hours=1)
            )
            
            print("--- SIMULACIÓN DE SMS ---")
            print(f"Enviando código {codigo_sms} al teléfono de {empleado.idusuarios.nombreusuario}")
            print("-------------------------")
            
            request.session['reset_user_id'] = empleado.idusuarios.idusuarios
            return redirect('ingresar_codigo')

        except (Usuario.DoesNotExist, Empleado.DoesNotExist):
            error_msg = 'El empleado no existe o no se encuentra activo.'
            return render(request, 'HTML/solicitar_usuario.html', {'error': error_msg})

    return render(request, 'HTML/solicitar_usuario.html')

def ingresar_codigo(request):
    """Segundo paso: el usuario ingresa el código recibido por SMS."""
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('solicitar_usuario')

    if request.method == 'POST':
        code_parts = [request.POST.get(f'code{i}') for i in range(1, 6)]
        submitted_code = "".join(filter(None, code_parts))

        try:
            token_obj = TokenRecuperacion.objects.get(
                usuario_id=user_id, 
                codigo_sms=submitted_code, 
                expiracion_codigo_sms__gte=timezone.now(),
                activo=True
            )
            
            host = request.get_host()
            verify_link = f"http://{host}/recuperar/verificar-email/{token_obj.token_email}/"
            
            print("--- SIMULACIÓN DE EMAIL ---")
            print(f"Enviando link de verificación a {token_obj.usuario.emailusuario}")
            print(f"Link SÍ, SOY YO: {verify_link}")
            print(f"Link NO, SOY YO: http://{host}/recuperar/acceso-denegado/")
            print("---------------------------")
            
            context = {'message': '¡Código correcto! Se ha enviado un mensaje a su correo para verificar su identidad.'}
            return render(request, 'HTML/ingresar_codigo.html', context)

        except TokenRecuperacion.DoesNotExist:
            RegistroSeguridad.objects.create(
                direccion_ip=obtener_ip(request),
                intento_usuario=Usuario.objects.get(idusuarios=user_id).nombreusuario,
                intento_contrasena=f"CÓDIGO SMS: {submitted_code}",
                motivo='Código de reseteo incorrecto o expirado.'
            )
            return render(request, 'HTML/ingresar_codigo.html', {'error': 'Código incorrecto o expirado.'})

    return render(request, 'HTML/ingresar_codigo.html')

def reenviar_codigo(request):
    """Reenvía un nuevo código SMS al usuario."""
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('solicitar_usuario')
    
    usuario = Usuario.objects.get(idusuarios=user_id)
    TokenRecuperacion.objects.filter(usuario=usuario, activo=True).update(activo=False)
    
    codigo_sms = str(random.randint(10000, 99999))
    expiracion = timezone.now() + timedelta(minutes=5)
    TokenRecuperacion.objects.create(
        usuario=usuario, codigo_sms=codigo_sms, expiracion_codigo_sms=expiracion,
        expiracion_token_email=timezone.now() + timedelta(hours=1)
    )
    print(f"--- RE-ENVIANDO CÓDIGO {codigo_sms} ---")
    return redirect('ingresar_codigo')

def verificar_email(request, token):
    """Verifica el token enviado por email."""
    try:
        token_obj = TokenRecuperacion.objects.get(
            token_email=token,
            expiracion_token_email__gte=timezone.now(),
            activo=True
        )
        request.session['reset_final_user_id'] = token_obj.usuario.idusuarios
        return redirect('cambiar_contrasena')
    except TokenRecuperacion.DoesNotExist:
        return redirect('acceso_denegado')

def cambiar_contrasena(request):
    """Paso final: el usuario establece una nueva contraseña."""
    user_id = request.session.get('reset_final_user_id')
    if not user_id:
        return redirect('iniciar_sesion')

    if request.method == 'POST':
        pass1 = request.POST.get('new_password1')
        pass2 = request.POST.get('new_password2')

        if not pass1 or not pass2 or pass1 != pass2:
            return render(request, 'HTML/cambiar_contrasena.html', {'error': 'Las contraseñas no coinciden o están vacías.'})
        
        usuario = Usuario.objects.get(idusuarios=user_id)
        usuario.passwordusuario = pass1
        usuario.save()
        
        TokenRecuperacion.objects.filter(usuario=usuario).update(activo=False)
        
        request.session.flush()
        return redirect('iniciar_sesion')

    return render(request, 'HTML/cambiar_contrasena.html')

def acceso_denegado(request):
    """Página que se muestra si el usuario cancela la recuperación o el token es inválido."""
    return render(request, 'HTML/acceso_denegado.html')

def crear_empleado_vista(request):
    herramientas = Herramienta.objects.all()
    context = {
        'herramientas': herramientas
    }
    return render(request, 'HTML/crear_empleado.html', context)