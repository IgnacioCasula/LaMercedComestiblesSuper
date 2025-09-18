from django.shortcuts import redirect
from django.contrib import messages

def permiso_requerido(roles_permitidos=None):
    """
    Decorador que verifica si el rol del usuario en sesión
    está en la lista de roles permitidos.
    """
    if roles_permitidos is None:
        roles_permitidos = []

    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            rol_usuario = request.session.get('rol_nombre')

            if not rol_usuario:
                messages.error(request, "Debe iniciar sesión para acceder a esta página.")
                return redirect('iniciar_sesion')

            if rol_usuario in roles_permitidos:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "No tienes los permisos necesarios para acceder a esta herramienta.")
                return redirect('inicio')
        return wrapper
    return decorator