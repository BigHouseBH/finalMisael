from django.db import models
from .turno import Turno
from .paciente import Paciente

class Recordatorio(models.Model):
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, related_name='recordatorios')
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='recordatorios')
    mensaje = models.TextField()
    leido = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Recordatorio'
        verbose_name_plural = 'Recordatorios'

    def __str__(self):
        return f"Recordatorio para {self.paciente.usuario.username} - {self.fecha_creacion.strftime('%d/%m/%Y %H:%M')}"