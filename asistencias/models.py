from django.db import models
from caja.models import Empleados, Roles

class Horario(models.Model):
    idhorario = models.AutoField(primary_key=True)
    empleado = models.ForeignKey(Empleados, on_delete=models.CASCADE, related_name="horarios")
    rol = models.ForeignKey(Roles, on_delete=models.CASCADE, related_name="horarios", null=True)
    nombre_horario = models.CharField(max_length=100, default="Horario Principal")
    
    class Meta:
        db_table = 'horarios'
        verbose_name = "Horario"
        verbose_name_plural = "Horarios"

    def __str__(self):
        return f"Horario de {self.empleado} para el rol {self.rol.nombrerol if self.rol else ''}"

class DiaHorario(models.Model):
    iddiahorario = models.AutoField(primary_key=True)
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE, related_name="dias")
    dia_semana = models.IntegerField() 
    semana_del_mes = models.IntegerField(default=1)

    class Meta:
        db_table = 'dias_horario'
        verbose_name = "Día de Horario"
        verbose_name_plural = "Días de Horario"

class TramoHorario(models.Model):
    idtramohorario = models.AutoField(primary_key=True)
    dia_horario = models.ForeignKey(DiaHorario, on_delete=models.CASCADE, related_name="tramos")
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        db_table = 'tramos_horario'
        verbose_name = "Tramo Horario"
        verbose_name_plural = "Tramos Horarios"