from apscheduler.schedulers.background import BackgroundScheduler
from app.tasks import actualizar_turnos

scheduler = BackgroundScheduler()

scheduler.add_job(
    actualizar_turnos,
    'cron',
    hour=0,
    minute=0,
    id='actualizar_turnos_diario',
    replace_existing=True
)

scheduler.start()