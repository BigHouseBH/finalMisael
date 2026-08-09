from django.utils import timezone
from datetime import timedelta
from app.models.turno import Turno
from app.models.recordatorios import Recordatorio

def actualizar_turnos():
    """Actualiza turnos pasados a 'finalizado'."""
    hoy = timezone.now().date()
    turnos_pasados = Turno.objects.filter(
        fecha_turno__lt=hoy,
        estado__in=['pendiente', 'confirmado']
    )
    count = turnos_pasados.update(estado='finalizado')
    print(f"{count} turnos actualizados a finalizado")
    return count

def generar_recordatorios_diarios():
    """Genera recordatorios para los turnos de mañana."""
    mañana = timezone.now().date() + timedelta(days=1)
    turnos_mañana = Turno.objects.filter(
        fecha_turno__date=mañana,
        estado='confirmado'
    )
    creados = 0
    for turno in turnos_mañana:
        mensaje = (
            f"Mañana tienes un turno con {turno.medico.nombre} {turno.medico.apellido} "
            f"a las {turno.fecha_hora.strftime('%H:%M')}."
        )
        _, created = Recordatorio.objects.get_or_create(
            turno=turno,
            paciente=turno.paciente,
            defaults={
                'mensaje': mensaje,
                'leido': False,
                'fecha_creacion': timezone.now()
            }
        )
        if created:
            creados += 1
    print(f"{creados} recordatorios generados para turnos de mañana")
    return creados