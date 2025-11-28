"""
Comando Django para cargar datos de prueba en la base de datos.

Ubicación: caja/management/commands/cargar_datos.py

Uso: python manage.py cargar_datos
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime, time, date, timedelta
from caja.models import (
    Roles, Usuarios, Empleados, UsuxRoles, Horario, 
    Asistencias, PeriodoNomina, DeudaNomina, RegistroNominaSemanal
)


class Command(BaseCommand):
    help = 'Carga datos de prueba: Área Depósito, puestos y empleado Luis Martinez'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando carga de datos...'))
        
        try:
            # ===== 1. CREAR ÁREA Y PUESTOS =====
            self.stdout.write('📂 Creando área "Depósito"...')
            
            # Verificar si ya existe el área
            if Roles.objects.filter(nombrearea='Deposito').exists():
                self.stdout.write(self.style.WARNING('⚠️  El área "Deposito" ya existe. Continuando...'))
            
            # Crear puesto: Control de Stock
            puesto_control, created = Roles.objects.get_or_create(
                nombrerol='Control de Stock',
                nombrearea='Deposito',
                defaults={
                    'descripcionrol': 'Puesto de Control de Stock con permisos: Stock | PermisosJSON: ["stock"] | Salario: $1500'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS('✅ Puesto "Control de Stock" creado'))
            else:
                self.stdout.write(self.style.WARNING('⚠️  Puesto "Control de Stock" ya existía'))
            
            # Crear puesto: Repositorio
            puesto_repo, created = Roles.objects.get_or_create(
                nombrerol='Repositorio',
                nombrearea='Deposito',
                defaults={
                    'descripcionrol': 'Puesto de Repositorio con permisos: Stock | PermisosJSON: ["stock"] | Salario: $2000'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS('✅ Puesto "Repositorio" creado'))
            else:
                self.stdout.write(self.style.WARNING('⚠️  Puesto "Repositorio" ya existía'))
            
            # ===== 2. CREAR USUARIO =====
            self.stdout.write('\n👤 Creando usuario Luis Martinez...')
            
            # Verificar si ya existe
            if Usuarios.objects.filter(dniusuario=46029381).exists():
                self.stdout.write(self.style.ERROR('❌ El usuario con DNI 46029381 ya existe. Abortando.'))
                return
            
            if Usuarios.objects.filter(emailusuario='waza@gmail.com').exists():
                self.stdout.write(self.style.ERROR('❌ El email waza@gmail.com ya está en uso. Abortando.'))
                return
            
            # Crear usuario
            usuario = Usuarios.objects.create(
                nombreusuario='Luis',
                apellidousuario='Martinez',
                emailusuario='waza@gmail.com',
                passwordusuario='hola123',
                dniusuario=46029381,
                telefono='3872739284',
                codigo_telefonico='+54',
                direccion='Pinares 200',
                fecha_nacimiento=date(1998, 8, 3),
                fecharegistrousuario=timezone.now().date(),
                imagenusuario=None
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Usuario creado: {usuario.nombreusuario} {usuario.apellidousuario}'))
            
            # ===== 3. CREAR EMPLEADO =====
            self.stdout.write('\n💼 Creando empleado...')
            
            empleado = Empleados.objects.create(
                idusuarios=usuario,
                cargoempleado='Control de Stock',
                salarioempleado=1500.0,  # Salario por hora
                fechacontratado=date(2024, 12, 7),
                estado='Trabajando'
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Empleado creado con salario de ${empleado.salarioempleado}/hora'))
            
            # ===== 4. ASIGNAR ROL =====
            self.stdout.write('\n🎭 Asignando rol...')
            
            UsuxRoles.objects.create(
                idusuarios=usuario,
                idroles=puesto_control
            )
            self.stdout.write(self.style.SUCCESS('✅ Rol "Control de Stock" asignado'))
            
            # ===== 5. CREAR HORARIOS =====
            self.stdout.write('\n🕐 Creando horarios...')
            
            # Horario: Lunes a Viernes 08:00 - 16:00
            dias_laborales = [0, 1, 2, 3, 4]  # Lunes a Viernes
            for dia in dias_laborales:
                Horario.objects.create(
                    empleado=empleado,
                    rol=puesto_control,
                    dia_semana=dia,
                    semana_del_mes=1,  # Todas las semanas
                    hora_inicio=time(8, 0),
                    hora_fin=time(16, 0)
                )
            
            self.stdout.write(self.style.SUCCESS('✅ Horarios creados: Lunes a Viernes 08:00 - 16:00'))
            
            # ===== 6. CREAR ASISTENCIAS (ÚLTIMAS 2 SEMANAS) =====
            self.stdout.write('\n📋 Creando asistencias de las últimas 2 semanas...')
            
            hoy = timezone.now().date()
            fecha_inicio_asistencias = hoy - timedelta(days=14)
            
            asistencias_creadas = 0
            fecha_actual = fecha_inicio_asistencias
            
            while fecha_actual <= hoy:
                dia_semana = fecha_actual.weekday()
                
                # Solo registrar asistencias en días laborales (Lunes a Viernes)
                if dia_semana in dias_laborales and fecha_actual >= empleado.fechacontratado:
                    # Simular variación de llegada (algunos días temprano, otros tarde)
                    import random
                    variacion_minutos = random.randint(-15, 20)  # Entre 15 min antes y 20 min tarde
                    
                    hora_entrada = time(8, max(0, min(59, variacion_minutos)))
                    hora_salida = time(16, random.randint(0, 15))  # Salida entre 16:00 y 16:15
                    
                    # No registrar salida si es hoy y estamos en horario laboral
                    if fecha_actual == hoy:
                        ahora = timezone.now().time()
                        if ahora < time(16, 0):
                            hora_salida = None
                    
                    Asistencias.objects.create(
                        idempleado=empleado,
                        fechaasistencia=fecha_actual,
                        horaentrada=hora_entrada,
                        horasalida=hora_salida,
                        rol=puesto_control
                    )
                    asistencias_creadas += 1
                
                fecha_actual += timedelta(days=1)
            
            self.stdout.write(self.style.SUCCESS(f'✅ {asistencias_creadas} asistencias creadas'))
            
            # ===== 7. CREAR PERÍODOS DE NÓMINA Y DEUDA =====
            self.stdout.write('\n💰 Configurando nóminas...')
            
            # Crear período actual (semana actual)
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fin_semana = inicio_semana + timedelta(days=6)
            
            periodo_actual, created = PeriodoNomina.objects.get_or_create(
                fecha_inicio=inicio_semana,
                fecha_fin=fin_semana,
                defaults={'cerrado': False}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Período actual creado: {inicio_semana} - {fin_semana}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️  Período actual ya existía'))
            
            # Crear períodos anteriores cerrados
            periodos_anteriores = 2
            for i in range(1, periodos_anteriores + 1):
                inicio = inicio_semana - timedelta(weeks=i)
                fin = inicio + timedelta(days=6)
                
                periodo, created = PeriodoNomina.objects.get_or_create(
                    fecha_inicio=inicio,
                    fecha_fin=fin,
                    defaults={
                        'cerrado': True,
                        'fecha_cierre': timezone.now()
                    }
                )
                
                if created:
                    # Calcular horas trabajadas en ese período
                    asistencias_periodo = Asistencias.objects.filter(
                        idempleado=empleado,
                        fechaasistencia__range=[inicio, fin]
                    )
                    
                    horas_trabajadas = 0
                    for asistencia in asistencias_periodo:
                        if asistencia.horaentrada and asistencia.horasalida:
                            entrada_dt = datetime.combine(asistencia.fechaasistencia, asistencia.horaentrada)
                            salida_dt = datetime.combine(asistencia.fechaasistencia, asistencia.horasalida)
                            horas = (salida_dt - entrada_dt).total_seconds() / 3600
                            horas_trabajadas += max(0, horas)
                    
                    monto_devengado = horas_trabajadas * empleado.salarioempleado
                    
                    # Crear registro semanal
                    RegistroNominaSemanal.objects.create(
                        empleado=empleado,
                        periodo=periodo,
                        rol=puesto_control,
                        horas_trabajadas=horas_trabajadas,
                        monto_devengado=monto_devengado
                    )
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'✅ Período {inicio} - {fin}: {horas_trabajadas:.1f}h = ${monto_devengado:.2f}'
                    ))
            
            # Crear/actualizar deuda acumulada
            deuda_total = RegistroNominaSemanal.objects.filter(
                empleado=empleado
            ).aggregate(total=Sum('monto_devengado'))['total'] or 0
            
            deuda, created = DeudaNomina.objects.get_or_create(
                empleado=empleado,
                defaults={'total_adeudado': deuda_total}
            )
            
            if not created:
                deuda.total_adeudado = deuda_total
                deuda.save()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Deuda acumulada: ${deuda_total:.2f}'))
            
            # ===== RESUMEN FINAL =====
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('✅ DATOS CARGADOS EXITOSAMENTE'))
            self.stdout.write('='*60)
            self.stdout.write(f'\n👤 Usuario: {usuario.nombreusuario} {usuario.apellidousuario}')
            self.stdout.write(f'📧 Email: {usuario.emailusuario}')
            self.stdout.write(f'🔑 Contraseña: hola123')
            self.stdout.write(f'🆔 DNI: {usuario.dniusuario}')
            self.stdout.write(f'\n💼 Puesto: {empleado.cargoempleado}')
            self.stdout.write(f'📂 Área: Deposito')
            self.stdout.write(f'💵 Salario: ${empleado.salarioempleado}/hora')
            self.stdout.write(f'📅 Fecha de inicio: {empleado.fechacontratado}')
            self.stdout.write(f'\n🕐 Horario: Lunes a Viernes 08:00 - 16:00')
            self.stdout.write(f'📋 Asistencias: {asistencias_creadas} registros')
            self.stdout.write(f'💰 Deuda acumulada: ${deuda_total:.2f}')
            self.stdout.write('\n' + '='*60 + '\n')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ ERROR: {str(e)}'))
            import traceback
            traceback.print_exc()