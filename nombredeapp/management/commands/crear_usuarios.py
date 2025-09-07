# ignaciocasula/lamercedcomestiblessuper/LaMercedComestiblesSuper-01f8d833acd495d85802e57720fa43f65e7b42b3/nombredeapp/management/commands/crear_usuarios.py

from django.core.management.base import BaseCommand
from datetime import date
from caja.models import Usuarios as Usuario, Empleados as Empleado, Roles as Rol, Usuariosxrol as UsuarioRol, Area, Herramienta, Permiso

class Command(BaseCommand):
    help = 'Crea usuarios de prueba con sus areas, puestos y permisos.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Iniciando la insercion de datos de prueba..."))

        # --- 1. Crear Areas ---
        area_caja, _ = Area.objects.get_or_create(nombrearea='Caja')
        area_admin, _ = Area.objects.get_or_create(nombrearea='Administracion')
        self.stdout.write("Areas creadas/verificadas.")

        # --- 2. Crear Puestos (Roles) ---
        puesto_super_caja, _ = Rol.objects.get_or_create(nombrerol='Supervisor de Caja', defaults={'area': area_caja})
        puesto_rrhh, _ = Rol.objects.get_or_create(nombrerol='Recursos Humanos', defaults={'area': area_admin})
        self.stdout.write("Puestos (Roles) creados/verificados.")
        
        # --- 3. Crear Herramientas y Permisos ---
        self.stdout.write("Creando herramientas y asignando permisos...")
        herramienta_crear_empleado, _ = Herramienta.objects.get_or_create(
            nombre='Crear Empleado',
            defaults={'url_nombre': 'crear_empleado', 'icono': 'fas fa-user-plus'}
        )
        Permiso.objects.get_or_create(rol=puesto_rrhh, herramienta=herramienta_crear_empleado)

        # --- LÍNEA CORREGIDA ---
        # Guardamos el nombre completo de la URL con el prefijo de la app 'caja'
        herramienta_caja, _ = Herramienta.objects.get_or_create(
            nombre='Caja',
            defaults={'url_nombre': 'caja:menu_caja', 'icono': 'fas fa-cash-register'}
        )

        herramienta_asistencias, _ = Herramienta.objects.get_or_create(
            nombre='Asistencias',
            defaults={'url_nombre': 'asistencias:ver_asistencias', 'icono': 'fas fa-clock'}
        )
        # Por defecto, se lo asignamos a ambos roles de ejemplo
        Permiso.objects.get_or_create(rol=puesto_super_caja, herramienta=herramienta_asistencias)
        Permiso.objects.get_or_create(rol=puesto_rrhh, herramienta=herramienta_asistencias)

        self.stdout.write("-> Permisos asignados correctamente.")

        # Por defecto, se lo asignamos a todos los roles para probar
        Permiso.objects.get_or_create(rol=puesto_super_caja, herramienta=herramienta_asistencias)
        Permiso.objects.get_or_create(rol=puesto_rrhh, herramienta=herramienta_asistencias)
        self.stdout.write(self.style.SUCCESS("-> Permiso 'Ver Asistencias' creado y asignado."))

        Permiso.objects.get_or_create(rol=puesto_super_caja, herramienta=herramienta_caja)
        self.stdout.write("-> Permisos asignados correctamente.")

        # --- 4. Crear Empleados ---
        self.stdout.write("Creando usuarios de prueba...")
        usuario_laura, created = Usuario.objects.get_or_create(
            nombreusuario='lgomez',
            defaults={'apellidousuario': 'Gomez', 'emailusuario': 'laura.gomez@ejemplo.com', 'passwordusuario': 'waza', 'dniusuario': 33111222, 'fecharegistrousuario': date.today()}
        )
        if created:
            Empleado.objects.create(idusuarios=usuario_laura, cargoempleado='Cajera Principal', salarioempleado=50000.00, fechacontratado=date.today())
            UsuarioRol.objects.create(idusuarios=usuario_laura, idroles=puesto_super_caja)

        usuario_ana, created = Usuario.objects.get_or_create(
            nombreusuario='arobles',
            defaults={'apellidousuario': 'Robles', 'emailusuario': 'ana.robles@ejemplo.com', 'passwordusuario': '777', 'dniusuario': 35555666, 'fecharegistrousuario': date.today()}
        )
        if created:
            Empleado.objects.create(idusuarios=usuario_ana, cargoempleado='Analista de RRHH', salarioempleado=65000.00, fechacontratado=date.today())
            UsuarioRol.objects.create(idusuarios=usuario_ana, idroles=puesto_rrhh)
        
        self.stdout.write(self.style.SUCCESS("\n¡Proceso finalizado!"))