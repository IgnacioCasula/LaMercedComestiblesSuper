from django.core.management.base import BaseCommand
from datetime import date, time
from caja.models import Usuarios, Empleados, Roles, UsuxRoles, Horario

class Command(BaseCommand):
    help = 'Crea usuarios de prueba con sus areas, puestos y horarios.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Iniciando la insercion de datos de prueba..."))

        # --- Crear Puestos (Roles) ---
        puesto_super_caja, _ = Roles.objects.get_or_create(nombrerol='Supervisor de Caja', defaults={'nombrearea': 'Caja'})
        puesto_rrhh, _ = Roles.objects.get_or_create(nombrerol='Recursos Humanos', defaults={'nombrearea': 'Administracion'})
        self.stdout.write("Puestos (Roles) creados/verificados.")
        
        # --- Crear Empleados y Horarios ---
        self.stdout.write("Creando usuarios de prueba y sus horarios...")
        
        # Usuario 1: Laura Gómez
        usuario_laura, created_laura = Usuarios.objects.get_or_create(
            nombreusuario='L',
            defaults={
                'apellidousuario': 'Gomez', 
                'emailusuario': 'laura.gomez@ejemplo.com', 
                'passwordusuario': 'waza', 
                'dniusuario': 33111222, 
                'fecharegistrousuario': date.today()
            }
        )
        if created_laura:
            empleado_laura = Empleados.objects.create(idusuarios=usuario_laura, cargoempleado='Cajera Principal', salarioempleado=50000.00, fechacontratado=date.today())
            UsuxRoles.objects.create(idusuarios=usuario_laura, idroles=puesto_super_caja)
            # Horario para Laura (Lunes a Viernes, 8-16h)
            for dia in range(5):
                for semana in range(1, 5): # 4 semanas del mes
                    Horario.objects.create(
                        empleado=empleado_laura, 
                        rol=puesto_super_caja, 
                        dia_semana=dia, 
                        semana_del_mes=semana, 
                        hora_inicio=time(8, 0), 
                        hora_fin=time(16, 0)
                    )
            self.stdout.write(self.style.SUCCESS(f"-> Usuario {usuario_laura.nombreusuario} creado con horario."))

        # Usuario 2: Ana Robles
        usuario_ana, created_ana = Usuarios.objects.get_or_create(
            nombreusuario='Ana',
            defaults={
                'apellidousuario': 'Robles', 
                'emailusuario': 'ana.robles@ejemplo.com', 
                'passwordusuario': '777', 
                'dniusuario': 35555666, 
                'fecharegistrousuario': date.today()
            }
        )
        if created_ana:
            empleado_ana = Empleados.objects.create(idusuarios=usuario_ana, cargoempleado='Analista de RRHH', salarioempleado=65000.00, fechacontratado=date.today())
            UsuxRoles.objects.create(idusuarios=usuario_ana, idroles=puesto_rrhh)
            # Horario para Ana (Lunes, Miércoles, Viernes 9-17h)
            for dia in [0, 2, 4]: 
                for semana in range(1, 5): # 4 semanas del mes
                    Horario.objects.create(
                        empleado=empleado_ana, 
                        rol=puesto_rrhh, 
                        dia_semana=dia, 
                        semana_del_mes=semana, 
                        hora_inicio=time(9, 0), 
                        hora_fin=time(17, 0)
                    )
            self.stdout.write(self.style.SUCCESS(f"-> Usuario {usuario_ana.nombreusuario} creado con horario."))
        
        self.stdout.write(self.style.SUCCESS("\n¡Proceso finalizado!"))