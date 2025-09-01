# ignaciocasula/lamercedcomestiblessuper/LaMercedComestiblesSuper-9e4cb265129870267e8e016db0b510984c444d8d/nombredeapp/management/commands/crear_usuarios.py
# nombredeapp/management/commands/crear_usuarios.py

from django.core.management.base import BaseCommand
from datetime import date
from caja.models import Usuarios as Usuario, Empleados as Empleado, Roles as Rol, Usuariosxrol as UsuarioRol, Area

class Command(BaseCommand):
    help = 'Crea usuarios de prueba con sus areas y puestos.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Iniciando la insercion de datos de prueba..."))

        # --- 1. Crear Areas ---
        area_caja, _ = Area.objects.get_or_create(nombrearea='Caja')
        area_ventas, _ = Area.objects.get_or_create(nombrearea='Ventas')
        area_admin, _ = Area.objects.get_or_create(nombrearea='Administracion')
        self.stdout.write("Areas creadas/verificadas.")

        # --- 2. Crear Puestos (Roles) y asignarlos a un Área ---
        puesto_cajero, _ = Rol.objects.get_or_create(nombrerol='Cajero', defaults={'area': area_caja})
        puesto_super_caja, _ = Rol.objects.get_or_create(nombrerol='Supervisor de Caja', defaults={'area': area_caja})
        puesto_repositor, _ = Rol.objects.get_or_create(nombrerol='Repositor', defaults={'area': area_ventas})
        puesto_gerente, _ = Rol.objects.get_or_create(nombrerol='Gerente de Ventas', defaults={'area': area_ventas})
        puesto_admin, _ = Rol.objects.get_or_create(nombrerol='Contador', defaults={'area': area_admin})
        self.stdout.write("Puestos (Roles) creados/verificados y asignados a sus áreas.")

        # --- 3. Crear Empleados y asignarles Puestos ---

        # Empleado 1: Laura Gomez
        usuario_laura, created = Usuario.objects.get_or_create(
            nombreusuario='lgomez',
            defaults={
                'apellidousuario': 'Gomez', 'emailusuario': 'laura.gomez@ejemplo.com',
                'passwordusuario': 'clave123', 'dniusuario': 33111222, 'telefono': '3874111222',
                'fecharegistrousuario': date.today()
            }
        )
        # CORRECCIÓN: Se añaden los campos obligatorios 'salarioempleado' y 'fechacontratado'
        Empleado.objects.get_or_create(
            idusuarios=usuario_laura, 
            defaults={
                'cargoempleado': 'Cajera Principal', 
                'estado': 'Trabajando',
                'salarioempleado': 50000.00,  # Valor de ejemplo
                'fechacontratado': date.today() # Valor de ejemplo
            }
        )
        UsuarioRol.objects.get_or_create(idusuarios=usuario_laura, idroles=puesto_super_caja)
        if created:
            self.stdout.write(self.style.SUCCESS("Usuario 1 (Laura Gomez) creado y asignado."))
        else:
            self.stdout.write(self.style.WARNING("Usuario 1 (Laura Gomez) ya existia."))


        # Empleado 2: Marcos Diaz
        usuario_marcos, created = Usuario.objects.get_or_create(
            nombreusuario='mdiaz',
            defaults={
                'apellidousuario': 'Diaz', 'emailusuario': 'marcos.diaz@ejemplo.com',
                'passwordusuario': 'clave456', 'dniusuario': 34333444, 'telefono': '3875333444',
                'fecharegistrousuario': date.today()
            }
        )
        # CORRECCIÓN: Se añaden los campos obligatorios 'salarioempleado' y 'fechacontratado'
        Empleado.objects.get_or_create(
            idusuarios=usuario_marcos, 
            defaults={
                'cargoempleado': 'Jefe de Salon', 
                'estado': 'Trabajando',
                'salarioempleado': 75000.00,  # Valor de ejemplo
                'fechacontratado': date.today() # Valor de ejemplo
            }
        )
        UsuarioRol.objects.get_or_create(idusuarios=usuario_marcos, idroles=puesto_gerente)
        UsuarioRol.objects.get_or_create(idusuarios=usuario_marcos, idroles=puesto_repositor)
        UsuarioRol.objects.get_or_create(idusuarios=usuario_marcos, idroles=puesto_admin)
        if created:
            self.stdout.write(self.style.SUCCESS("Usuario 2 (Marcos Diaz) creado y asignado."))
        else:
            self.stdout.write(self.style.WARNING("Usuario 2 (Marcos Diaz) ya existia."))


        self.stdout.write(self.style.SUCCESS("\n¡Proceso finalizado!"))