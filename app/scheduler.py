from apscheduler.schedulers.background import BackgroundScheduler
from app.tasks import actualizar_turnos, generar_recordatorios_diarios

scheduler = BackgroundScheduler()

# Tarea 1: Actualizar turnos pasados a las 00:00
scheduler.add_job(
    actualizar_turnos,
    'cron',
    hour=0,
    minute=0,
    id='actualizar_turnos_diario',
    replace_existing=True
)

# Tarea 2: Generar recordatorios para turnos de mañana a las 00:05
scheduler.add_job(
    generar_recordatorios_diarios,
    'cron',
    hour=0,
    minute=5,
    id='generar_recordatorios_diarios',
    replace_existing=True
)

scheduler.start()