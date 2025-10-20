from datetime import timedelta
import random
import json
import string

from django.shortcuts import render, redirect
from django.utils import timezone
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction

from caja.models import Usuarios, Roles, UsuxRoles, Empleados, Horario, Caja


MAX_INTENTOS = 3
BLOQUEO_MINUTOS = 5
CODIGO_EXPIRA_MINUTOS = 5


def _get_session_dict(request: HttpRequest, key: str, default: dict) -> dict:
    data = request.session.get(key)
    if not isinstance(data, dict):
        data = default.copy()
        request.session[key] = data
    return data


def _get_caja_abierta(usuario_id):
    """Verifica si hay una caja abierta para el usuario actual"""
    try:
        caja_abierta = Caja.objects.filter(
            idusuarios_id=usuario_id,
            fechacierrecaja__isnull=True
        ).exists()
        return caja_abierta
    except Exception:
        return False


def _verificar_autenticacion(request: HttpRequest) -> bool:
    """Verifica si el usuario está autenticado"""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return False
    
    usuario = Usuarios.objects.filter(idusuarios=usuario_id).first()
    return usuario is not None


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

        estado['intentos'] = 0
        estado['bloqueado_hasta'] = None
        request.session['login_estado'] = estado

        request.session['usuario_id'] = usuario.idusuarios
        request.session['nombre_usuario'] = usuario.nombreusuario

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
    
    roles_usuario = list(
        Roles.objects.filter(usuxroles__idusuarios_id=usuario_id).values_list('nombrerol', flat=True)
    )
    
    rol_actual = None
    if rol_id:
        rol_obj = Roles.objects.filter(idroles=rol_id).first()
        if rol_obj:
            rol_actual = rol_obj.nombrerol
    
    # Determinar permisos
    is_admin = 'Administrador' in roles_usuario or 'Recursos Humanos' in roles_usuario or len(roles_usuario) > 2
    
    # Permisos
    has_caja = False
    has_registrar_venta = False
    has_gestion_stock = False
    
    if is_admin:
        has_caja = True
        has_registrar_venta = True
        has_gestion_stock = True
    else:
        has_registrar_venta = 'Vendedor' in roles_usuario or 'Registrar Venta' in roles_usuario
        has_caja = has_registrar_venta or 'Supervisor de Caja' in roles_usuario or 'Caja' in roles_usuario
        has_gestion_stock = 'Gestor de Inventario' in roles_usuario or 'Gestión de Stock' in roles_usuario or 'Stock' in roles_usuario

    caja_abierta = _get_caja_abierta(usuario_id)

    context = {
        'nombre_usuario': nombre_usuario,
        'rol_nombre': rol_actual,
        'is_admin': is_admin,
        'has_caja': has_caja,
        'has_registrar_venta': has_registrar_venta,
        'has_gestion_stock': has_gestion_stock,
        'caja_abierta': caja_abierta,
        'debug_roles': roles_usuario,
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
    """Cierra la sesión con un periodo de gracia de 2 minutos."""
    usuario_id = request.session.get('usuario_id')
    respuesta = redirect('login')

    if usuario_id:
        expira = timezone.now() + timedelta(minutes=2)
        valor = f"{usuario_id}|{expira.isoformat()}"
        respuesta.set_signed_cookie(
            key='grace_logout',
            value=valor,
            salt='logout-grace',
            max_age=130,
            httponly=True,
            samesite='Lax',
        )

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
    """Devuelve todas las áreas con sus puestos y permisos."""
    try:
        areas = Roles.objects.values('nombrearea').distinct().order_by('nombrearea')
        
        resultado = []
        for area in areas:
            area_nombre = area['nombrearea']
            puestos = Roles.objects.filter(nombrearea=area_nombre).order_by('nombrerol')
            
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
                
                puestos_data.append({
                    'id': puesto.idroles,
                    'nombre': puesto.nombrerol,
                    'permisos': list(set(permisos))
                })
            
            resultado.append({
                'id': area_nombre,
                'nombre': area_nombre,
                'puestos': puestos_data
            })
        
        return JsonResponse(resultado, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@transaction.atomic
def api_crear_area(request):
    """Crea una nueva área."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre_area = data.get('nombre', '').strip()
            
            if not nombre_area:
                return JsonResponse({'error': 'El nombre del área es obligatorio.'}, status=400)
            
            if Roles.objects.filter(nombrearea__iexact=nombre_area).exists():
                return JsonResponse({'error': 'Ya existe un área con este nombre.'}, status=400)
            
            return JsonResponse({
                'id': nombre_area,
                'nombre': nombre_area,
                'message': 'Área creada correctamente. Ahora puedes añadir puestos.'
            }, status=201)
            
        except Exception as e:
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
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@transaction.atomic
def api_eliminar_area(request, area_nombre):
    """Elimina un área (solo si no tiene puestos)."""
    if request.method == 'DELETE':
        try:
            if Roles.objects.filter(nombrearea=area_nombre).exists():
                return JsonResponse({
                    'error': 'No puedes eliminar un área que tiene puestos. Elimina primero los puestos.'
                }, status=400)
            
            return JsonResponse({'message': 'Área eliminada correctamente.'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@transaction.atomic
def api_crear_puesto_nuevo(request):
    """Crea un nuevo puesto con permisos."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre_puesto = data.get('nombre', '').strip()
            area_id = data.get('area_id')
            permisos = data.get('permisos', [])
            
            if not all([nombre_puesto, area_id]):
                return JsonResponse({'error': 'Faltan datos obligatorios.'}, status=400)
            
            if Roles.objects.filter(nombrerol__iexact=nombre_puesto, nombrearea=area_id).exists():
                return JsonResponse({'error': 'Ya existe un puesto con este nombre en esta área.'}, status=400)
            
            permisos_desc = ', '.join([p.replace('_', ' ').title() for p in permisos]) if permisos else 'Sin permisos'
            descripcion = f'Puesto de {nombre_puesto} con permisos: {permisos_desc}'
            
            nuevo_puesto = Roles.objects.create(
                nombrerol=nombre_puesto,
                nombrearea=area_id,
                descripcionrol=descripcion
            )
            
            return JsonResponse({
                'id': nuevo_puesto.idroles,
                'nombre': nuevo_puesto.nombrerol,
                'permisos': permisos,
                'message': 'Puesto creado correctamente.'
            }, status=201)
            
        except Exception as e:
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
            
            if not nombre_puesto:
                return JsonResponse({'error': 'El nombre del puesto es obligatorio.'}, status=400)
            
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
            puesto.descripcionrol = f'Puesto de {nombre_puesto} con permisos: {permisos_desc}'
            puesto.save()
            
            return JsonResponse({
                'id': puesto.idroles,
                'nombre': puesto.nombrerol,
                'permisos': permisos,
                'message': 'Puesto actualizado correctamente.'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@transaction.atomic
def api_eliminar_puesto(request, puesto_id):
    """Elimina un puesto."""
    if request.method == 'DELETE':
        try:
            try:
                puesto = Roles.objects.get(idroles=puesto_id)
            except Roles.DoesNotExist:
                return JsonResponse({'error': 'El puesto no existe.'}, status=404)
            
            empleados_count = Empleados.objects.filter(cargoempleado=puesto.nombrerol).count()
            usuarios_count = UsuxRoles.objects.filter(idroles=puesto).count()
            
            if empleados_count > 0 or usuarios_count > 0:
                return JsonResponse({
                    'error': f'No puedes eliminar este puesto. Hay {empleados_count + usuarios_count} empleado(s) asignado(s).'
                }, status=400)
            
            puesto.delete()
            
            return JsonResponse({'message': 'Puesto eliminado correctamente.'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def api_puestos_por_area_con_permisos(request, area_id):
    """Devuelve todos los puestos de un área con sus permisos."""
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
            
            data.append({
                'id': puesto.idroles,
                'nombre': puesto.nombrerol,
                'permisos': list(set(permisos))
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
        
        nuevo_empleado = Empleados.objects.create(
            idusuarios=nuevo_usuario,
            cargoempleado=puesto_seleccionado.get('nombre', 'Sin Puesto'),
            salarioempleado=0,
            fechacontratado=timezone.now().date(),
            estado='Trabajando'
        )

        puesto_id = puesto_seleccionado.get('id')
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
            'username': username
        }, status=201)

    except Exception as e:
        return JsonResponse({'error': f'Ocurrió un error inesperado: {str(e)}'}, status=500)


def lista_empleados_view(request: HttpRequest) -> HttpResponse:
    """Vista temporal para lista de empleados."""
    if not _verificar_autenticacion(request):
        messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
        return redirect('login')
    
    return render(request, 'HTML/lista_empleados.html', {
        'mensaje': 'Lista de empleados - En desarrollo'
    })


def gestion_stock_view(request: HttpRequest) -> HttpResponse:
    """Vista para gestión de stock."""
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