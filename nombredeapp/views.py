from django.shortcuts import render, redirect
from caja.models import Usuarios as Usuario, Empleados as Empleado, Roles as Rol, Usuariosxrol as UsuarioRol, RegistroSeguridad, TokenRecuperacion, Asistencias, Permiso, Herramienta
from django.http import JsonResponse
from caja.models import Area, Roles
from django.utils import timezone
from datetime import timedelta, date, datetime
from django.core.mail import send_mail
from django.db import transaction
import random
import json
import string
from asistencias.models import Horario, DiaHorario, TramoHorario

def obtener_ip(request):
    """Obtiene la dirección IP real del cliente."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def registrar_asistencia_entrada(empleado, rol_id):
    """Crea un nuevo registro de asistencia para un empleado y rol."""
    Asistencias.objects.filter(
        idempleado=empleado,
        rol_id=rol_id,
        horasalida__isnull=True
    ).update(horasalida=timezone.localtime().time())

    Asistencias.objects.create(
        idempleado=empleado,
        rol_id=rol_id,
        fechaasistencia=timezone.localtime().date(),
        horaentrada=timezone.localtime().time()
    )

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
                        conteo_roles = UsuarioRol.objects.filter(idusuarios=usuario).count()

                        if conteo_roles > 1:
                            request.session['pre_auth_usuario_id'] = usuario.idusuarios
                            return redirect('seleccionar_rol')
                        
                        elif conteo_roles == 1:
                            rol_relacion = UsuarioRol.objects.filter(idusuarios=usuario).first()
                            rol = rol_relacion.idroles
                            request.session['usuario_id'] = usuario.idusuarios
                            request.session['nombre_usuario'] = usuario.nombreusuario
                            request.session['apellido_usuario'] = usuario.apellidousuario
                            request.session['rol_id'] = rol.idroles
                            request.session['rol_nombre'] = rol.nombrerol
                            registrar_asistencia_entrada(empleado, rol.idroles)

                            return redirect('inicio')
                        else:
                            request.session['usuario_id'] = usuario.idusuarios
                            request.session['nombre_usuario'] = usuario.nombreusuario
                            request.session['apellido_usuario'] = usuario.apellidousuario
                            request.session['rol_nombre'] = "Sin puesto asignado"
                            return redirect('inicio')
                            
                    else:
                        return render(request, 'HTML/login.html', {'error': f'Acceso denegado. Su estado es: {empleado.estado}.'})

                except Empleado.DoesNotExist:
                    return render(request, 'HTML/login.html', {'error': 'Este usuario no es un empleado válido.'})
            else:
                return render(request, 'HTML/login.html', {'error': 'Ha ingresado mal la contraseña.'})

        except Usuario.DoesNotExist:
            return render(request, 'HTML/login.html', {'error': 'El empleado no existe.'})

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
        empleado = Empleado.objects.get(idusuarios=usuario)

        request.session['usuario_id'] = usuario.idusuarios
        request.session['nombre_usuario'] = usuario.nombreusuario
        request.session['apellido_usuario'] = usuario.apellidousuario
        request.session['rol_id'] = rol_seleccionado.idroles
        request.session['rol_nombre'] = rol_seleccionado.nombrerol
        del request.session['pre_auth_usuario_id']
        
        registrar_asistencia_entrada(empleado, rol_seleccionado.idroles)
        
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
    return render(request, 'HTML/seleccionar_rol.html', context)


def cerrar_sesion(request):
    """Cierra la sesión del usuario y registra la hora de salida para el rol actual."""
    usuario_id = request.session.get('usuario_id')
    rol_id = request.session.get('rol_id')

    if usuario_id and rol_id:
        try:
            empleado = Empleado.objects.get(idusuarios_id=usuario_id)
            asistencia_abierta = Asistencias.objects.filter(
                idempleado=empleado,
                rol_id=rol_id,
                horasalida__isnull=True
            ).order_by('-fechaasistencia', '-horaentrada').first()

            if asistencia_abierta:
                asistencia_abierta.horasalida = timezone.localtime().time()
                asistencia_abierta.save()

        except Empleado.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error al registrar salida: {e}")

    request.session.flush()
    return redirect('iniciar_sesion')

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

def api_areas(request):
    """Devuelve todas las áreas, opcionalmente filtradas por un término de búsqueda."""
    query = request.GET.get('q', '').strip()
    if query:
        areas = Area.objects.filter(nombrearea__icontains=query)
    else:
        areas = Area.objects.all()
    
    data = [{'id': area.idarea, 'nombre': area.nombrearea} for area in areas]
    return JsonResponse(data, safe=False)

def api_crear_area(request):
    """Crea una nueva área."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre_area = data.get('nombre').strip()
            if not nombre_area:
                return JsonResponse({'error': 'El nombre no puede estar vacío.'}, status=400)
            if Area.objects.filter(nombrearea__iexact=nombre_area).exists():
                return JsonResponse({'error': 'Ya existe un área con este nombre.'}, status=400)
            nueva_area = Area.objects.create(nombrearea=nombre_area)
            return JsonResponse({'id': nueva_area.idarea, 'nombre': nueva_area.nombrearea}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def api_puestos_por_area(request, area_id):
    """Devuelve todos los puestos para un área específica."""
    puestos = Roles.objects.filter(area_id=area_id)
    data = [{'id': puesto.idroles, 'nombre': puesto.nombrerol} for puesto in puestos]
    return JsonResponse(data, safe=False)

def api_crear_puesto(request):
    """Crea un nuevo puesto y lo asocia a un área."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre_puesto = data.get('nombre').strip()
            area_id = data.get('area_id')

            if not all([nombre_puesto, area_id]):
                return JsonResponse({'error': 'Faltan datos (nombre o area_id).'}, status=400)
            if Roles.objects.filter(nombrerol__iexact=nombre_puesto, area_id=area_id).exists():
                 return JsonResponse({'error': 'Ya existe un puesto con este nombre en esta área.'}, status=400)
            
            nuevo_puesto = Roles.objects.create(nombrerol=nombre_puesto, area_id=area_id)
            return JsonResponse({'id': nuevo_puesto.idroles, 'nombre': nuevo_puesto.nombrerol}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@transaction.atomic
def api_registrar_empleado(request):
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
            return JsonResponse({'error': 'Faltan datos personales obligatorios (nombre, apellido, email, DNI).'}, status=400)

        if Usuario.objects.filter(emailusuario__iexact=email).exists():
            return JsonResponse({'error': 'El correo electrónico ya está en uso.'}, status=400)
        
        if Usuario.objects.filter(dniusuario=dni).exists():
            return JsonResponse({'error': 'El DNI ya está registrado.'}, status=400)

        username = (nombre.split(' ')[0] + apellido.replace(' ', '')).lower()
        temp_username = username
        counter = 1
        while Usuario.objects.filter(nombreusuario=temp_username).exists():
            temp_username = f"{username}{counter}"
            counter += 1
        username = temp_username
        
        password = ''.join(random.choices(string.digits, k=5))

        nuevo_usuario = Usuario.objects.create(
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
        
        nuevo_empleado = Empleado.objects.create(
            idusuarios=nuevo_usuario,
            cargoempleado=puesto_seleccionado.get('nombre', 'Sin Puesto'),
            salarioempleado=0,
            fechacontratado=timezone.now().date(),
            estado='Trabajando'
        )

        puesto_id = puesto_seleccionado.get('id')
        if puesto_id:
            puesto_base = Roles.objects.get(idroles=puesto_id)
            permisos_ids_seleccionados = data.get('permisos', [])
            rol_personalizado = Roles.objects.create(
                nombrerol=f"{puesto_base.nombrerol} ({nuevo_usuario.nombreusuario})",
                area=puesto_base.area,
                descripcionrol=f"Rol personalizado para el usuario {nuevo_usuario.nombreusuario}"
            )
            UsuarioRol.objects.create(idusuarios=nuevo_usuario, idroles=rol_personalizado)
            
            for herramienta_id in permisos_ids_seleccionados:
                herramienta = Herramienta.objects.get(idherramienta=herramienta_id)
                Permiso.objects.create(rol=rol_personalizado, herramienta=herramienta)
            
            nuevo_empleado.cargoempleado = rol_personalizado.nombrerol
            nuevo_empleado.save()
        
            horario_data = data.get('horario', {})
            if horario_data:
                dias_semana_map = {'Lu': 0, 'Ma': 1, 'Mi': 2, 'Ju': 3, 'Vi': 4, 'Sa': 5, 'Do': 6}
                
                horario_principal = Horario.objects.create(empleado=nuevo_empleado, rol=rol_personalizado)
                
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
                        dia_horario_obj, created = DiaHorario.objects.get_or_create(
                            horario=horario_principal,
                            dia_semana=day,
                            semana_del_mes=week_number
                        )
                        
                        tramos = schedule_data.get(color, [])
                        for tramo in tramos:
                            if tramo.get('start') and tramo.get('end'):
                                TramoHorario.objects.create(
                                    dia_horario=dia_horario_obj,
                                    hora_inicio=tramo['start'],
                                    hora_fin=tramo['end']
                                )

        send_mail(
            subject='¡Bienvenido! Tus credenciales de acceso',
            message=f"Hola {nombre},\n\n¡Te damos la bienvenida al sistema! A continuación encontrarás tus datos para iniciar sesión:\n\nNombre de Usuario: {username}\nContraseña Temporal: {password}\n\nTe recomendamos cambiar tu contraseña después de tu primer inicio de sesión.\n\nSaludos,\nEl equipo de Supermercado.",
            from_email='noreply@supermercado.com',
            recipient_list=[email],
            fail_silently=False,
        )

        return JsonResponse({'message': f'¡Empleado {nombre} {apellido} creado exitosamente!', 'username': username}, status=201)

    except Exception as e:
        return JsonResponse({'error': f'Ocurrió un error inesperado: {str(e)}'}, status=500)