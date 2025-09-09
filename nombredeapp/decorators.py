# nombredeapp/decorators.py

from django.shortcuts import redirect
from django.contrib import messages
from caja.models import Permiso

def permiso_requerido(nombre_url_herramienta):
    """
    Decorador que verifica si el rol del usuario en sesión tiene permiso
    para acceder a una herramienta específica, identificada por su 'url_nombre'.
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):

            print(f"🔍 DEBUG DECORADOR: Verificando permiso para {nombre_url_herramienta}")

            print(f"🔍 DEBUG DECORADOR: rol_id en sesión = {request.session.get('rol_id')}")

            if 'rol_id' not in request.session:
                print("🔍 DEBUG DECORADOR: No hay rol_id en sesión, redirigiendo a login")
                 
                messages.error(request, "Debe iniciar sesión para acceder a esta página.")
                return redirect('iniciar_sesion')

            rol_id_actual = request.session.get('rol_id')

            print(f"🔍 DEBUG DECORADOR: rol_id_actual = {rol_id_actual}")

            tiene_permiso = Permiso.objects.filter(
                rol_id=rol_id_actual,
                herramienta__url_nombre=nombre_url_herramienta
            ).exists()

            print(f"🔍 DEBUG DECORADOR: tiene_permiso = {tiene_permiso}")
            
            if tiene_permiso:

                print("🔍 DEBUG DECORADOR: ✅ Permiso concedido, ejecutando vista")

                return view_func(request, *args, **kwargs)
            else:

                print("🔍 DEBUG DECORADOR: ❌ Sin permisos, redirigiendo a inicio")

                messages.error(request, "No tiene los permisos necesarios para acceder a esta herramienta.")
                return redirect('inicio')
        return wrapper
    return decorator