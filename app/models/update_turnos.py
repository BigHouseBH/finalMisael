#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'turnoya.settings')
django.setup()

from app.models import Turno
from django.utils import timezone


def limpiar_turnos_pasados():
    hoy = timezone.now().date()
    
    turnos = Turno.objects.filter(
        fecha_hora__date__lt=hoy,
        estado__in=[Turno.PENDIENTE, Turno.CONFIRMADO]
    )
    
    cantidad = turnos.count()
    
    if cantidad > 0:
        turnos.update(estado=Turno.NO_ASISTIO)
        print(f'Se marcaron {cantidad} turnos como no asistidos.')
    else:
        print('No hay turnos pasados para marcar.')
    
    return cantidad


if __name__ == '__main__':
    print('Actualizando turnos...')
    limpiar_turnos_pasados()
    print('Actualizacion completada.')