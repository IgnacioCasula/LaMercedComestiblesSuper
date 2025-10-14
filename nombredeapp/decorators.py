from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from caja.models import Roles, UsuxRoles, Usuarios


def permiso_requerido(roles_permitidos=None):
    roles_permitidos = roles_permitidos or []

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            usuario_id = request.session.get('usuario_id')
            if not usuario_id:
                messages.error(request, 'Debes iniciar sesión.')
                return redirect('login')

            # Si hay rol en sesión, validar
            rol_sel_id = request.session.get('rol_id')
            if roles_permitidos:
                if rol_sel_id:
                    try:
                        rol_nombre = Roles.objects.filter(idroles=rol_sel_id).values_list('nombrerol', flat=True).first()
                    except Exception:
                        rol_nombre = None
                    if rol_nombre in roles_permitidos:
                        return view_func(request, *args, **kwargs)
                # Sin rol o no coincide: verificar si el usuario posee alguno de los roles permitidos
                posee = UsuxRoles.objects.filter(idusuarios_id=usuario_id, idroles__nombrerol__in=roles_permitidos).exists()
                if not posee:
                    messages.error(request, 'Acceso denegado.')
                    return redirect('login')
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator



