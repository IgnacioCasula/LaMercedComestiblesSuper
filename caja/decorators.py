# caja/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import Usuarios, Roles

def permiso_requerido(roles_permitidos=None):
    """
    Decorador para verificar que el usuario tenga uno de los roles permitidos.
    
    Args:
        roles_permitidos: Lista de nombres de roles que pueden acceder a la vista
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Verificar autenticación
            usuario_id = request.session.get('usuario_id')
            if not usuario_id:
                messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
                return redirect('login')
            
            # Obtener usuario
            try:
                usuario = Usuarios.objects.get(idusuarios=usuario_id)
            except Usuarios.DoesNotExist:
                messages.error(request, 'Usuario no encontrado.')
                return redirect('login')
            
            # Si no hay roles específicos requeridos, permitir acceso
            if not roles_permitidos:
                return view_func(request, *args, **kwargs)
            
            # Obtener roles del usuario
            roles_usuario = list(
                Roles.objects.filter(usuxroles__idusuarios=usuario)
                .values_list('nombrerol', flat=True)
            )
            
            # Verificar si el usuario tiene alguno de los roles permitidos
            # También permitir acceso a administradores y RRHH
            roles_admin = ['Administrador', 'Recursos Humanos']
            
            tiene_permiso = (
                any(rol in roles_permitidos for rol in roles_usuario) or
                any(rol in roles_admin for rol in roles_usuario)
            )
            
            if not tiene_permiso:
                messages.error(request, f'No tienes permisos para acceder a esta sección. Se requiere uno de estos roles: {", ".join(roles_permitidos)}')
                return redirect('inicio')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator