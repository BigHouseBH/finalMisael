from django.urls import path
from . import views
from .views_historial import HistorialView
from .views_turnos import (
    SeleccionarEspecialidadView,
    MedicosDisponiblesView,
    TurnosDisponiblesView,
    ConfirmarTurnoView,
    AceptarTurnoView,
    RechazarTurnoView,
    CancelarTurnoView,
    RegistrarAsistenciaView,
    DetalleTurnoView,
)
from .views_recordatorios import ListaRecordatoriosView, MarcarLeidoView

app_name = "app"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("medicos/", views.ListaMedicosView.as_view(), name="lista_medicos"),
    path("accounts/registro/", views.RegistroUsuarioView.as_view(), name="registro"),
    path("perfil/", views.PerfilUsuarioView.as_view(), name="perfil_usuario"),
    path("pacientes/", views.ListaPacientesView.as_view(), name="lista_pacientes"),
    path("medicos/<int:pk>/", views.DetalleMedicoView.as_view(), name="detalle_medico"),
    path("turnos/", views.ListaTurnosView.as_view(), name="lista_turnos"),
    path("ausencias/", views.ListaAusenciasView.as_view(), name="lista_ausencias"),
    path("ausencias/nueva/", views.NuevaAusenciaView.as_view(), name="nueva_ausencia"),
    path("ausencias/<int:pk>/eliminar/", views.EliminarAusenciaView.as_view(), name="eliminar_ausencia"),
    path('paciente/<int:pk>/historial/', HistorialView.as_view(), name='historial'),

    # --- Flujo de pedir turno (desde views_turnos) ---
    path("especialidades/", SeleccionarEspecialidadView.as_view(), name="seleccionar_especialidad"),
    path("especialidad/<int:especialidad_id>/medicos/", MedicosDisponiblesView.as_view(), name="medicos_disponibles"),
    path("medico/<int:medico_id>/turnos/", TurnosDisponiblesView.as_view(), name="turnos_disponibles"),
    path("turno/confirmar/<int:medico_id>/<str:fecha>/<str:hora>/", ConfirmarTurnoView.as_view(), name="confirmar_turno"),
    path("turnos/<int:pk>/aceptar/", AceptarTurnoView.as_view(), name="aceptar_turno"),
    path("turnos/<int:pk>/rechazar/", RechazarTurnoView.as_view(), name="rechazar_turno"),
    path("turnos/<int:pk>/cancelar/", CancelarTurnoView.as_view(), name="cancelar_turno"),
    path('turno/<int:pk>/registrar-asistencia/', RegistrarAsistenciaView.as_view(), name='registrar_asistencia'),

    # --- Recordatorios ---
    path('recordatorios/', ListaRecordatoriosView.as_view(), name='recordatorios'),
    path('recordatorios/<int:pk>/marcar-leido/', MarcarLeidoView.as_view(), name='marcar_leido'),
    path('turno/<int:pk>/', DetalleTurnoView.as_view(), name='detalle_turno'),
]