from django.core.management.base import BaseCommand
from app.tasks import actualizar_turnos, generar_recordatorios_diarios

class Command(BaseCommand):
    help = "Ejecuta todas las tareas de tasks.py (actualizar turnos y generar recordatorios)"

    def handle(self, *args, **options):
        self.stdout.write("1. Ejecutando actualización de turnos...")
        actualizados = actualizar_turnos()
        self.stdout.write(f"   -> {actualizados} turnos procesados.")

        self.stdout.write("2. Generando recordatorios diarios...")
        recordatorios = generar_recordatorios_diarios()
        self.stdout.write(f"   -> {recordatorios} recordatorios generados.")

        self.stdout.write(self.style.SUCCESS("Todas las tareas de tasks.py fueron ejecutadas con éxito."))
