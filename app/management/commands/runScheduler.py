from django.core.management.base import BaseCommand
from app.scheduler import scheduler

class Command(BaseCommand):
    help = "Ejecuta el scheduler de tareas programadas"

    def handle(self, *args, **options):
        self.stdout.write("Scheduler iniciado...")
        scheduler.start()
        self.stdout.write("Scheduler corriendo. Presione Ctrl+C para detener.")
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            self.stdout.write("Scheduler detenido.")
            scheduler.shutdown()