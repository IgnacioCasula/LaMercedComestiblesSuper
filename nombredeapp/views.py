# Create your views here.
from django.shortcuts import render, redirect
from .models import Usuarios, Empleados, SecurityLog, Usuariosxrol, Roles

# Función para obtener la IP del cliente
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
                        # RUTA CORREGIDA
                        return render(request, 'HTML/login.html', {'error': f'Acceso denegado. Su estado es: {empleado.estado}.'})

                except Empleados.DoesNotExist:
                    SecurityLog.objects.create(
                        ip_address=ip_address, username_attempt=username_attempt, password_attempt=password_attempt,
                        reason='Usuario existe pero no es empleado.'
                    )
                    # RUTA CORREGIDA
                    return render(request, 'HTML/login.html', {'error': 'Este usuario no es un empleado válido.'})
            else:
                SecurityLog.objects.create(
                    ip_address=ip_address, username_attempt=username_attempt, password_attempt=password_attempt,
                    reason='Contraseña incorrecta.'
                )
                # RUTA CORREGIDA
                return render(request, 'HTML/login.html', {'error': 'Ha ingresado mal la contraseña.'})

        except Usuarios.DoesNotExist:
            SecurityLog.objects.create(
                ip_address=ip_address, username_attempt=username_attempt, password_attempt=password_attempt,
                reason='El empleado no existe.'
            )
            # RUTA CORREGIDA
            return render(request, 'HTML/login.html', {'error': 'El empleado no existe.'})

    # RUTA CORREGIDA
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

    # RUTA CORREGIDA
    return render(request, 'HTML/seleccionar_rol.html', {'roles_usuario': roles_del_usuario})

def inicio_view(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    # RUTA CORREGIDA
    return render(request, 'HTML/inicio.html')

def logout_view(request):
    request.session.flush()
    return redirect('login')
