from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import time

from caja.models import Usuarios, Roles, UsuxRoles, Empleados, Horario


class Command(BaseCommand):
    help = "Crea el usuario administrador por defecto (admin/admin123) si no existe"

    def add_arguments(self, parser):
        parser.add_argument('--usuario', default='admin')
        parser.add_argument('--apellido', default='admin')
        parser.add_argument('--email', default='admin@gmail.com')
        parser.add_argument('--password', default='admin123')
        parser.add_argument('--dni', type=int, default=99999999)
        parser.add_argument('--telefono', default='3875551234', help='Número de teléfono del usuario')
        parser.add_argument('--area', default='Administración')
        parser.add_argument('--rol', default='Administrador')
        parser.add_argument('--sueldo', type=float, default=None, help='Sueldo del empleado (si no se especifica, se extrae del rol)')
        parser.add_argument('--hora-inicio', default='09:00', help='Hora de inicio del horario (formato HH:MM)')
        parser.add_argument('--hora-fin', default='18:00', help='Hora de fin del horario (formato HH:MM)')
        parser.add_argument('--dias', default='0,1,2,3,4', help='Días de la semana (0=Lun, 6=Dom). Ej: 0,1,2,3,4 para Lun-Vie')

    def handle(self, *args, **options):
        nombreusuario = options['usuario']
        apellidousuario = options['apellido']
        email = options['email']
        password = options['password']
        dni = options['dni']
        telefono = options['telefono']
        area = options['area']
        rol_nombre = options['rol']
        sueldo_manual = options['sueldo']

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
                telefono=telefono,
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

        # EXTRAER SALARIO DEL PUESTO O USAR EL MANUAL
        salario_empleado = 0
        
        if sueldo_manual is not None:
            # Si se especificó un sueldo manual, usar ese
            salario_empleado = sueldo_manual
            self.stdout.write(self.style.SUCCESS(f'💰 Usando sueldo manual: ${salario_empleado:,.2f}'))
        else:
            # Intentar extraer el salario de la descripción del rol
            if rol.descripcionrol and 'Salario: $' in rol.descripcionrol:
                try:
                    salario_str = rol.descripcionrol.split('Salario: $')[1]
                    if '|' in salario_str:
                        salario_str = salario_str.split('|')[0].strip()
                    else:
                        salario_str = salario_str.strip()
                    salario_str = salario_str.replace(',', '').replace(' ', '')
                    salario_empleado = float(salario_str)
                    self.stdout.write(self.style.SUCCESS(f'💰 Sueldo extraído del rol: ${salario_empleado:,.2f}'))
                except (ValueError, IndexError, AttributeError) as e:
                    self.stdout.write(self.style.WARNING(f'⚠️  No se pudo extraer el salario del rol: {e}'))
                    salario_empleado = 0
            else:
                self.stdout.write(self.style.WARNING('⚠️  El rol no tiene salario definido en su descripción'))
                salario_empleado = 0

        # CREAR EL EMPLEADO con el salario correcto
        empleado, created = Empleados.objects.get_or_create(
            idusuarios=usuario,
            defaults={
                'cargoempleado': rol_nombre,
                'salarioempleado': salario_empleado,
                'fechacontratado': timezone.now().date(),
                'estado': 'Trabajando'
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Empleado creado exitosamente para {usuario.nombreusuario}'))
            self.stdout.write(self.style.SUCCESS(f'   Salario asignado: ${salario_empleado:,.2f}'))
        else:
            # Si ya existía, actualizar el salario si es diferente
            if empleado.salarioempleado != salario_empleado and salario_empleado > 0:
                empleado.salarioempleado = salario_empleado
                empleado.save()
                self.stdout.write(self.style.SUCCESS(f'✅ Salario actualizado a: ${salario_empleado:,.2f}'))
            else:
                self.stdout.write(self.style.WARNING('⚠️  El empleado ya existía'))

        # CREAR HORARIOS PARA EL EMPLEADO
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
        self.stdout.write(self.style.SUCCESS(f'Teléfono: {telefono}'))
        self.stdout.write(self.style.SUCCESS(f'Rol: {area} - {rol_nombre}'))
        self.stdout.write(self.style.SUCCESS(f'Salario: ${salario_empleado:,.2f}'))
        self.stdout.write(self.style.SUCCESS(f'Horario: Lunes a Viernes, 9:00 - 18:00'))
        self.stdout.write(self.style.SUCCESS('=' * 50))