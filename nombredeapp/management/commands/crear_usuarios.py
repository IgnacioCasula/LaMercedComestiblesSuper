# ignaciocasula/lamercedcomestiblessuper/LaMercedComestiblesSuper-9e4cb265129870267e8e016db0b510984c444d8d/nombredeapp/management/commands/crear_usuarios.py
# nombredeapp/management/commands/crear_usuarios.py

from django.core.management.base import BaseCommand
from datetime import date
# Se añaden Herramienta y Permiso a los modelos importados
from caja.models import Usuarios as Usuario, Empleados as Empleado, Roles as Rol, Usuariosxrol as UsuarioRol, Area, Herramienta, Permiso

class Command(BaseCommand):
    help = 'Crea usuarios de prueba con sus areas, puestos y permisos.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Iniciando la insercion de datos de prueba..."))

        # --- 1. Crear Areas ---
        area_caja, _ = Area.objects.get_or_create(nombrearea='Caja')
        area_ventas, _ = Area.objects.get_or_create(nombrearea='Ventas')
        area_admin, _ = Area.objects.get_or_create(nombrearea='Administracion')
        self.stdout.write("Areas creadas/verificadas.")

        # --- 2. Crear Puestos (Roles) y asignarlos a un Área ---
        puesto_super_caja, _ = Rol.objects.get_or_create(nombrerol='Supervisor de Caja', defaults={'area': area_caja})
        puesto_gerente, _ = Rol.objects.get_or_create(nombrerol='Gerente de Ventas', defaults={'area': area_ventas})
        puesto_repositor, _ = Rol.objects.get_or_create(nombrerol='Repositor', defaults={'area': area_ventas})
        puesto_admin, _ = Rol.objects.get_or_create(nombrerol='Contador', defaults={'area': area_admin})
        # Nuevo Rol para Recursos Humanos
        puesto_rrhh, _ = Rol.objects.get_or_create(nombrerol='Recursos Humanos', defaults={'area': area_admin})
        self.stdout.write("Puestos (Roles) creados/verificados y asignados a sus áreas.")

        # --- 3. Crear Herramientas y Permisos ---
        self.stdout.write("Creando herramientas y permisos...")
        # Se define la herramienta "Crear Empleado"
        herramienta_crear_empleado, _ = Herramienta.objects.get_or_create(
            nombre='Crear Empleado',
            defaults={
                'url_nombre': 'crear_empleado', # Debe coincidir con el 'name' de la URL
                'icono': 'fa-solid fa-user-plus'  # Un ícono de FontAwesome
            }
        )
        # Se asigna el permiso de la herramienta al rol de RRHH
        Permiso.objects.get_or_create(rol=puesto_rrhh, herramienta=herramienta_crear_empleado)
        self.stdout.write(self.style.SUCCESS("Permiso 'Crear Empleado' asignado al rol 'Recursos Humanos'."))


        # --- 4. Crear Empleados y asignarles Puestos ---

        # Empleado 1: Laura Gomez (sin cambios)
        usuario_laura, created = Usuario.objects.get_or_create(
            nombreusuario='lgomez',
            defaults={
                'apellidousuario': 'Gomez', 'emailusuario': 'laura.gomez@ejemplo.com',
                'passwordusuario': 'clave123', 'dniusuario': 33111222, 'telefono': '3874111222',
                'fecharegistrousuario': date.today()
            }
        )
        Empleado.objects.get_or_create(
            idusuarios=usuario_laura, 
            defaults={
                'cargoempleado': 'Cajera Principal', 'estado': 'Trabajando',
                'salarioempleado': 50000.00, 'fechacontratado': date.today()
            }
        )
        UsuarioRol.objects.get_or_create(idusuarios=usuario_laura, idroles=puesto_super_caja)
        if created: self.stdout.write(self.style.SUCCESS("Usuario 1 (Laura Gomez) creado y asignado."))

        # Empleado 2: Marcos Diaz (sin cambios)
        usuario_marcos, created = Usuario.objects.get_or_create(
            nombreusuario='mdiaz',
            defaults={
                'apellidousuario': 'Diaz', 'emailusuario': 'marcos.diaz@ejemplo.com',
                'passwordusuario': 'clave456', 'dniusuario': 34333444, 'telefono': '3875333444',
                'fecharegistrousuario': date.today()
            }
        )
        Empleado.objects.get_or_create(
            idusuarios=usuario_marcos, 
            defaults={
                'cargoempleado': 'Jefe de Salon', 'estado': 'Trabajando',
                'salarioempleado': 75000.00, 'fechacontratado': date.today()
            }
        )
        UsuarioRol.objects.get_or_create(idusuarios=usuario_marcos, idroles=puesto_gerente)
        UsuarioRol.objects.get_or_create(idusuarios=usuario_marcos, idroles=puesto_repositor)
        UsuarioRol.objects.get_or_create(idusuarios=usuario_marcos, idroles=puesto_admin)
        if created: self.stdout.write(self.style.SUCCESS("Usuario 2 (Marcos Diaz) creado y asignado."))

        # --- NUEVO USUARIO CON PERMISOS ---
        # Empleado 3: Ana Robles
        usuario_ana, created = Usuario.objects.get_or_create(
            nombreusuario='arobles',
            defaults={
                'apellidousuario': 'Robles', 'emailusuario': 'ana.robles@ejemplo.com',
                'passwordusuario': 'clave789', 'dniusuario': 35555666, 'telefono': '3876555666',
                'fecharegistrousuario': date.today()
            }
        )
        Empleado.objects.get_or_create(
            idusuarios=usuario_ana,
            defaults={
                'cargoempleado': 'Analista de RRHH', 'estado': 'Trabajando',
                'salarioempleado': 65000.00, 'fechacontratado': date.today()
            }
        )
        # Se le asigna el rol de Recursos Humanos
        UsuarioRol.objects.get_or_create(idusuarios=usuario_ana, idroles=puesto_rrhh)
        if created:
            self.stdout.write(self.style.SUCCESS("Usuario 3 (Ana Robles) creada y asignada al rol de RRHH."))
        else:
            self.stdout.write(self.style.WARNING("Usuario 3 (Ana Robles) ya existia."))


        self.stdout.write(self.style.SUCCESS("\n¡Proceso finalizado!"))