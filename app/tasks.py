# app/tasks.py
from django.utils import timezone
from app.models.turno import Turno

def actualizar_turnos():
    hoy = timezone.now().date()
    turnos_pasados = Turno.objects.filter(
        fecha_turno__lt=hoy,
        estado__in=['pendiente', 'confirmado']
    )
    count = turnos_pasados.update(estado='finalizado')
    print(f"{count} turnos actualizados a finalizado")
    return count