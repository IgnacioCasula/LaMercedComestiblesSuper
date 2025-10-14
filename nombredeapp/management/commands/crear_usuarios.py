from django.core.management.base import BaseCommand
from django.utils import timezone

from caja.models import Usuarios, Roles, UsuxRoles


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
        rol, _ = Roles.objects.get_or_create(nombrerol=rol_nombre, defaults={'nombrearea': area})

        # Vincular rol al usuario (UsuxRoles)
        if not UsuxRoles.objects.filter(idusuarios=usuario, idroles=rol).exists():
            UsuxRoles.objects.create(idusuarios=usuario, idroles=rol)
            self.stdout.write(self.style.SUCCESS(f'Rol "{rol_nombre}" asignado.'))
        else:
            self.stdout.write(self.style.WARNING('El usuario ya tiene ese rol.'))

        self.stdout.write(self.style.SUCCESS('Listo.'))


