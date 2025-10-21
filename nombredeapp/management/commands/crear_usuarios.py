from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import time

from caja.models import Usuarios, Roles, UsuxRoles, Empleados, Horario


class Command(BaseCommand):
    help = "Crea el usuario administrador por defecto (admin/admin123) si no existe"

    def add_arguments(self, parser):
        parser.add_argument('--usuario', default='admin')
        parser.add_argument('--apellido', default='admin')
        parser.add_argument('--email', default='admin@local')
        parser.add_argument('--password', default='admin123')
        parser.add_argument('--dni', type=int, default=99999999)
        parser.add_argument('--area', default='Administración')
        parser.add_argument('--rol', default='Administrador')
        parser.add_argument('--hora-inicio', default='09:00', help='Hora de inicio del horario (formato HH:MM)')
        parser.add_argument('--hora-fin', default='18:00', help='Hora de fin del horario (formato HH:MM)')
        parser.add_argument('--dias', default='0,1,2,3,4', help='Días de la semana (0=Lun, 6=Dom). Ej: 0,1,2,3,4 para Lun-Vie')

    def handle(self, *args, **options):
        nombreusuario = options['usuario']
        apellidousuario = options['apellido']
        email = options['email']
        password = options['password']
        dni = options['dni']
        area = options['area']
        rol_nombre = options['rol']

        # Crear/obtener usuario
        usuario = Usuarios.objects.filter(nombreusuario=nombreusuario).first()
        if usuario:
            self.stdout.write(self.style.WARNING('Usuario ya existe.'))
        else:
            # Asegurar DNI único
            dni_candidato = dni
            while Usuarios.objects.filter(dniusuario=dni_candidato).exists():
                dni_candidato += 1
            usuario = Usuarios(
                nombreusuario=nombreusuario,
                apellidousuario=apellidousuario,
                emailusuario=email,
                passwordusuario=password,
                fecharegistrousuario=timezone.now().date(),
                dniusuario=dni_candidato,
            )
            usuario.save()
            self.stdout.write(self.style.SUCCESS(f'Usuario creado: {usuario.nombreusuario}'))

        # Crear/obtener rol
        rol, _ = Roles.objects.get_or_create(
            nombrerol=rol_nombre, 
            defaults={
                'nombrearea': area,
                'descripcionrol': f'Rol de {rol_nombre} con acceso completo al sistema'
            }
        )

        # Vincular rol al usuario (UsuxRoles)
        if not UsuxRoles.objects.filter(idusuarios=usuario, idroles=rol).exists():
            UsuxRoles.objects.create(idusuarios=usuario, idroles=rol)
            self.stdout.write(self.style.SUCCESS(f'Rol "{rol_nombre}" asignado.'))
        else:
            self.stdout.write(self.style.WARNING('El usuario ya tiene ese rol.'))

        # CREAR EL EMPLEADO (esto debe estar DENTRO del método handle)
        empleado, created = Empleados.objects.get_or_create(
            idusuarios=usuario,
            defaults={
                'cargoempleado': rol_nombre,
                'salarioempleado': 0,
                'fechacontratado': timezone.now().date(),
                'estado': 'Trabajando'
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Empleado creado exitosamente para {usuario.nombreusuario}'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  El empleado ya existía'))

        # CREAR HORARIOS PARA EL EMPLEADO
        # Verificar si ya tiene horarios
        horarios_existentes = Horario.objects.filter(empleado=empleado).count()
        
        if horarios_existentes == 0:
            # Crear horario de Lunes a Viernes, 9:00 - 18:00
            # Semana 1, 2, 3 y 4 del mes
            horarios_creados = 0
            
            for semana in range(1, 5):  # Semanas 1, 2, 3, 4
                for dia in range(0, 5):  # Lunes (0) a Viernes (4)
                    Horario.objects.create(
                        empleado=empleado,
                        rol=rol,
                        dia_semana=dia,
                        semana_del_mes=semana,
                        hora_inicio=time(9, 0),  # 9:00 AM
                        hora_fin=time(18, 0)     # 6:00 PM
                    )
                    horarios_creados += 1
            
            self.stdout.write(self.style.SUCCESS(f'✅ {horarios_creados} horarios creados (Lun-Vie, 9:00-18:00, todas las semanas)'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  El empleado ya tiene {horarios_existentes} horarios asignados'))

        self.stdout.write(self.style.SUCCESS(''))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('✅ CONFIGURACIÓN COMPLETA'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(f'Usuario: {nombreusuario}'))
        self.stdout.write(self.style.SUCCESS(f'Contraseña: {password}'))
        self.stdout.write(self.style.SUCCESS(f'Email: {email}'))
        self.stdout.write(self.style.SUCCESS(f'Rol: {area} - {rol_nombre}'))
        self.stdout.write(self.style.SUCCESS(f'Horario: Lunes a Viernes, 9:00 - 18:00'))
        self.stdout.write(self.style.SUCCESS('=' * 50))