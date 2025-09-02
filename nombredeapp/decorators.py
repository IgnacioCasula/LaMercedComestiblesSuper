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
            if 'rol_id' not in request.session:
                messages.error(request, "Debe iniciar sesión para acceder a esta página.")
                return redirect('iniciar_sesion')

            rol_id_actual = request.session.get('rol_id')

            tiene_permiso = Permiso.objects.filter(
                rol_id=rol_id_actual,
                herramienta__url_nombre=nombre_url_herramienta
            ).exists()
            
            if tiene_permiso:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "No tiene los permisos necesarios para acceder a esta herramienta.")
                return redirect('inicio')
        return wrapper
    return decorator