from django.db import models
from django.contrib.auth.models import User
from .medico import Medico
from .paciente import Paciente


class Turno(models.Model):
    """Representa un turno médico agendado."""

    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    CANCELADO = "cancelado"
    ATENDIDO = "atendido"
    NO_ASISTIO = "no_asistio"
    
    ESTADOS = [
        (PENDIENTE, "Pendiente"),
        (CONFIRMADO, "Confirmado"),
        (CANCELADO, "Cancelado"),
        (ATENDIDO, "Atendido"),
        (NO_ASISTIO, "No asistió"),
    ]
    
    asistio = models.BooleanField(
        null=True,
        blank=True,
        help_text="True si el paciente asistió, False si no, Null si aún no se sabe"
    )

    medico = models.ForeignKey(Medico, on_delete=models.CASCADE)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default=PENDIENTE)
    motivo = models.TextField()
    observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="turnos_creados",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["fecha_hora"]

    def __str__(self):
        return (
            f"Turno de {self.paciente} con {self.medico} "
            f"el {self.fecha_hora:%Y-%m-%d %H:%M}"
        )

    @classmethod
    def validate(cls, medico, paciente, fecha_hora, motivo,
        estado=PENDIENTE, observaciones="", instance=None):
        errors = []

        if not medico:
            errors.append("El médico es obligatorio.")
        if not paciente:
            errors.append("El paciente es obligatorio.")
        if not fecha_hora:
            errors.append("La fecha y hora son obligatorias.")
        if not motivo or not motivo.strip():
            errors.append("El motivo es obligatorio.")
        if estado not in dict(cls.ESTADOS):
            errors.append("El estado del turno no es válido.")

        # Defensa en profundidad: no permitir dos turnos activos del mismo
        # médico en el mismo horario (un turno cancelado libera el espacio).
        if medico and fecha_hora:
            query = cls.objects.filter(
                medico=medico, fecha_hora=fecha_hora
            ).exclude(estado=cls.CANCELADO)
            if instance:
                query = query.exclude(pk=instance.pk)
            if query.exists():
                errors.append("Ya existe un turno para ese médico en ese horario.")

        return errors

    @classmethod
    def new(cls, medico, paciente, fecha_hora, motivo,
            estado=PENDIENTE, observaciones="", creado_por=None):
        errors = cls.validate(medico, paciente, fecha_hora, motivo, estado, observaciones)
        if errors:
            return None, errors

        turno = cls.objects.create(
            medico=medico,
            paciente=paciente,
            fecha_hora=fecha_hora,
            estado=estado,
            motivo=motivo.strip(),
            observaciones=(observaciones or "").strip(),
            creado_por=creado_por,
        )
        return turno, []

    def update(self, medico, paciente, fecha_hora, motivo,
        estado=None, observaciones=None):
        estado = estado if estado is not None else self.estado
        observaciones = observaciones if observaciones is not None else self.observaciones

        errors = self.__class__.validate(
            medico, paciente, fecha_hora, motivo, estado, observaciones, instance=self
        )
        if errors:
            return errors

        self.medico = medico
        self.paciente = paciente
        self.fecha_hora = fecha_hora
        self.motivo = motivo.strip()
        self.estado = estado
        self.observaciones = (observaciones or "").strip()
        self.save()
        return []

    # --- Transiciones de estado (usadas por las vistas) ---

    def aceptar(self):
        """El médico confirma un turno pendiente."""
        self.estado = self.CONFIRMADO
        self.save()

    def rechazar(self):
        """El médico rechaza un turno pendiente.

        Reutiliza la transición a 'cancelado' (no hay estado 'rechazado').
        """
        self.estado = self.CANCELADO
        self.save()

    def cancelar(self):
        """El paciente cancela un turno propio."""
        self.estado = self.CANCELADO
        self.save()

    def marcar_asistencia(self, asistio=True):
        """Marca el turno como atendido o no asistió."""
        if asistio:
            self.estado = self.ATENDIDO
        else:
            self.estado = self.NO_ASISTIO
        self.save()
