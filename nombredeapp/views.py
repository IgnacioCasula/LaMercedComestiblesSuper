# Create your views here.
from django.shortcuts import render, redirect
from .models import Usuarios, Empleados, SecurityLog, Usuariosxrol, Roles, PasswordResetToken
from django.utils import timezone
from datetime import timedelta
import random

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def login_view(request):
    if request.method == 'POST':
        username_attempt = request.POST.get('username')
        password_attempt = request.POST.get('password')
        ip_address = get_client_ip(request)

        try:
            usuario = Usuarios.objects.get(nombreusuario=username_attempt)
            
            if usuario.passwordusuario == password_attempt:
                try:
                    empleado = Empleados.objects.get(usuario=usuario)
                    if empleado.estado == 'Trabajando':
                        roles_count = Usuariosxrol.objects.filter(usuario=usuario).count()

                        if roles_count > 1:
                            request.session['pre_auth_usuario_id'] = usuario.idusuarios
                            return redirect('seleccionar_rol')
                        else:
                            rol_relacion = Usuariosxrol.objects.filter(usuario=usuario).first()
                            request.session['usuario_id'] = usuario.idusuarios
                            request.session['nombre_usuario'] = f"{usuario.nombreusuario} {usuario.apellidousuario}"
                            if rol_relacion:
                                request.session['rol_id'] = rol_relacion.rol.idroles
                                request.session['rol_nombre'] = rol_relacion.rol.nombrerol
                            else:
                                request.session['rol_nombre'] = "Sin puesto asignado"
                            return redirect('inicio')
                            
                    else:
                        SecurityLog.objects.create(
                            ip_address=ip_address, username_attempt=username_attempt, password_attempt=password_attempt,
                            reason=f'Intento de login de empleado no activo. Estado: {empleado.estado}'
                        )
                        return render(request, 'HTML/login.html', {'error': f'Acceso denegado. Su estado es: {empleado.estado}.'})

                except Empleados.DoesNotExist:
                    SecurityLog.objects.create(
                        ip_address=ip_address, username_attempt=username_attempt, password_attempt=password_attempt,
                        reason='Usuario existe pero no es empleado.'
                    )
                    return render(request, 'HTML/login.html', {'error': 'Este usuario no es un empleado válido.'})
            else:
                SecurityLog.objects.create(
                    ip_address=ip_address, username_attempt=username_attempt, password_attempt=password_attempt,
                    reason='Contraseña incorrecta.'
                )
                return render(request, 'HTML/login.html', {'error': 'Ha ingresado mal la contraseña.'})

        except Usuarios.DoesNotExist:
            SecurityLog.objects.create(
                ip_address=ip_address, username_attempt=username_attempt, password_attempt=password_attempt,
                reason='El empleado no existe.'
            )
            return render(request, 'HTML/login.html', {'error': 'El empleado no existe.'})

    return render(request, 'HTML/login.html')

def seleccionar_rol_view(request):
    usuario_id = request.session.get('pre_auth_usuario_id')
    if not usuario_id:
        return redirect('login')
    
    usuario = Usuarios.objects.get(idusuarios=usuario_id)
    roles_del_usuario = Usuariosxrol.objects.filter(usuario=usuario)

    if request.method == 'POST':
        rol_id_seleccionado = request.POST.get('rol_id')
        rol_seleccionado = Roles.objects.get(idroles=rol_id_seleccionado)

        request.session['usuario_id'] = usuario.idusuarios
        request.session['nombre_usuario'] = f"{usuario.nombreusuario} {usuario.apellidousuario}"
        request.session['rol_id'] = rol_seleccionado.idroles
        request.session['rol_nombre'] = rol_seleccionado.nombrerol
        del request.session['pre_auth_usuario_id']

        return redirect('inicio')
    return render(request, 'HTML/seleccionar_rol.html', {'roles_usuario': roles_del_usuario})

def inicio_view(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    return render(request, 'HTML/inicio.html')

def logout_view(request):
    request.session.flush()
    return redirect('login')

def solicitar_usuario_view(request):
    if request.method == 'POST':
        username = request.POST.get('username_from_login') or request.POST.get('username')
        
        if not username:
            return render(request, 'HTML/solicitar_usuario.html', {'error': 'Debe ingresar un nombre de usuario.'})

        try:
            usuario = Usuarios.objects.get(nombreusuario=username)
            empleado = Empleados.objects.get(usuario=usuario, estado='Trabajando')

            PasswordResetToken.objects.filter(usuario=empleado.usuario, is_active=True).update(is_active=False)

            sms_code = str(random.randint(10000, 99999))
            expires_at = timezone.now() + timedelta(minutes=5)
            
            PasswordResetToken.objects.create(
                usuario=empleado.usuario,
                sms_code=sms_code,
                sms_code_expires_at=expires_at,
                email_token_expires_at=timezone.now() + timedelta(hours=1)
            )
            
            print("--- SIMULACIÓN DE SMS ---")
            print(f"Enviando código {sms_code} al teléfono de {empleado.usuario.nombreusuario}")
            print("-------------------------")
            
            request.session['reset_user_id'] = empleado.usuario.idusuarios
            return redirect('ingresar_codigo')

        except (Usuarios.DoesNotExist, Empleados.DoesNotExist):
            error_msg = 'El empleado no existe o no se encuentra activo.'
            return render(request, 'HTML/solicitar_usuario.html', {'error': error_msg})

    return render(request, 'HTML/solicitar_usuario.html')


def ingresar_codigo_view(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('solicitar_usuario')

    if request.method == 'POST':
        code_parts = [request.POST.get(f'code{i}') for i in range(1, 6)]
        submitted_code = "".join(code_parts)

        try:
            token_obj = PasswordResetToken.objects.get(
                usuario_id=user_id, 
                sms_code=submitted_code, 
                sms_code_expires_at__gte=timezone.now(),
                is_active=True
            )
            
            host = request.get_host()
            verify_link = f"http://{host}/verificar-email/{token_obj.email_token}/"
            
            print("--- SIMULACIÓN DE EMAIL ---")
            print(f"Enviando link de verificación a {token_obj.usuario.emailusuario}")
            print(f"Link SÍ, SOY YO: {verify_link}")
            print(f"Link NO, SOY YO: http://{host}/acceso-denegado/")
            print("---------------------------")
            
            context = {
                'message': '¡Código correcto! Se ha enviado un mensaje a su correo para verificar su identidad.'
            }
            return render(request, 'HTML/ingresar_codigo.html', context)

        except PasswordResetToken.DoesNotExist:
            SecurityLog.objects.create(
                ip_address=get_client_ip(request),
                username_attempt=Usuarios.objects.get(idusuarios=user_id).nombreusuario,
                password_attempt=f"CÓDIGO SMS: {submitted_code}",
                reason='Código de reseteo incorrecto o expirado.'
            )
            return render(request, 'HTML/ingresar_codigo.html', {'error': 'Código incorrecto o expirado.'})

    return render(request, 'HTML/ingresar_codigo.html')

def reenviar_codigo_view(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('solicitar_usuario')
    
    usuario = Usuarios.objects.get(idusuarios=user_id)
    PasswordResetToken.objects.filter(usuario=usuario, is_active=True).update(is_active=False)
    sms_code = str(random.randint(10000, 99999))
    expires_at = timezone.now() + timedelta(minutes=5)
    PasswordResetToken.objects.create(
        usuario=usuario, sms_code=sms_code, sms_code_expires_at=expires_at,
        email_token_expires_at=timezone.now() + timedelta(hours=1)
    )
    print(f"--- RE-ENVIANDO CÓDIGO {sms_code} ---")
    return redirect('ingresar_codigo')


def verificar_email_view(request, token):
    try:
        token_obj = PasswordResetToken.objects.get(
            email_token=token,
            email_token_expires_at__gte=timezone.now(),
            is_active=True
        )
        request.session['reset_final_user_id'] = token_obj.usuario.idusuarios
        return redirect('cambiar_contrasena')
    except PasswordResetToken.DoesNotExist:
        return redirect('acceso_denegado')


def cambiar_contrasena_view(request):
    user_id = request.session.get('reset_final_user_id')
    if not user_id:
        return redirect('login')

    if request.method == 'POST':
        pass1 = request.POST.get('new_password1')
        pass2 = request.POST.get('new_password2')

        if pass1 != pass2:
            return render(request, 'HTML/cambiar_contrasena.html', {'error': 'Las contraseñas no coinciden.'})
        
        usuario = Usuarios.objects.get(idusuarios=user_id)
        usuario.passwordusuario = pass1
        usuario.save()
        
        PasswordResetToken.objects.filter(usuario=usuario).update(is_active=False)
        
        request.session.flush()
        return redirect('login')

    return render(request, 'HTML/cambiar_contrasena.html')


def acceso_denegado_view(request):
    return render(request, 'HTML/acceso_denegado.html')
