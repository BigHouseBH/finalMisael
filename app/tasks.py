from django.utils import timezone
from datetime import timedelta
from app.models.turno import Turno
from app.models.recordatorios import Recordatorio

def actualizar_turnos():
    """Actualiza turnos pasados a 'cancelado'."""
    pasadoFecha = timezone.localdate() - timedelta(days=1)

    turnos_Pasados = Turno.objects.filter(
        fecha_hora__date__lte=pasadoFecha,
        estado__in=['pendiente', 'confirmado']
    )

    reportePendiente = "Cancelado automáticamente: El médico no aceptó la solicitud a tiempo."

    reporteConfirmado = "Cancelado automáticamente: venció el plazo programado sin registro de atención por parte del profesional."

    count=0
    for pasado in turnos_Pasados:#reporta la cancelacion automatica

        if (pasado.estado == 'pendiente'):
            pasado.observaciones = reportePendiente
        elif (pasado.estado == 'confirmado'):
            pasado.observaciones = reporteConfirmado
            pasado.asistio = False

        pasado.estado = "cancelado"
        pasado.save() # Guardar cambios 

        Recordatorio.objects.get_or_create(#actualiza el recordatorio utilizando la observacion que tiene el mensaje correspondiente
            turno=pasado,
            paciente=pasado.paciente,
            mensaje=pasado.observaciones
        )
        count += 1
    


    print(f"{count} turnos actualizados a cancelado")
    return count

def generar_recordatorios_diarios():
    """Genera recordatorios para los turnos de mañana."""
    mañana = timezone.localdate() + timedelta(days=1) # mañana = fechaActual + 1Dia
    turnos_mañana = Turno.objects.filter(#Filtra los turnos que son para mañana y estan confirmados
        fecha_hora__date=mañana,
        estado='confirmado'
    )

    creados = 0
    for turno in turnos_mañana: #Recorre los turnos de mañana
        #Arma el mensaje de recordatorio
        mensaje = (
            f"Mañana tienes un turno con {turno.medico.nombre} {turno.medico.apellido} "
            f"a las {turno.fecha_hora.strftime('%H:%M')}."
        )
        #Crea el recordatorio
        _, created = Recordatorio.objects.get_or_create(
            turno=turno,
            paciente=turno.paciente,
            defaults={#carga el diccionario
                'mensaje': mensaje,
                'leido': False,
                'fecha_creacion': timezone.now()
            }
        )
        if created:#creadosCOntador++
            creados += 1
    print(f"{creados} recordatorios generados para turnos de mañana")
    return creados