from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView

from .models import Especialidad, Medico, Paciente, Turno, Ausencia
from .views import PerfilPacienteRequiredMixin, DIAS_CALENDARIO, slots_libres_de_medico# ==================== FLUJO DE PEDIR TURNO ====================


class SeleccionarEspecialidadView(PerfilPacienteRequiredMixin, ListView):
    """Paso 1: el paciente elige una especialidad."""

    model = Especialidad
    template_name = "clinica/seleccionar_especialidad.html"
    context_object_name = "especialidades"
    ordering = ["nombre"]


class MedicosDisponiblesView(PerfilPacienteRequiredMixin, ListView):
    """Paso 2: médicos de la especialidad con al menos un turno libre en 15 días."""

    model = Medico
    template_name = "clinica/medicos_disponibles.html"
    context_object_name = "medicos"

    def get_queryset(self):
        especialidad_id = self.kwargs.get("especialidad_id")
        if not especialidad_id:
            return Medico.objects.none()
        hoy = timezone.localdate()
        ahora = timezone.now()
        medicos = Medico.objects.filter(especialidad_id=especialidad_id)
        disponibles = []
        for medico in medicos:
            tiene_disponibilidad = False
            for i in range(DIAS_CALENDARIO + 1):
                fecha = hoy + timedelta(days=i)
                slots = slots_libres_de_medico(medico, fecha)
                if fecha == hoy:
                    slots = [s for s in slots if s > ahora]
                if slots:
                    tiene_disponibilidad = True
                    break
            if tiene_disponibilidad:
                disponibles.append(medico)
        return disponibles

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["especialidad"] = get_object_or_404(
            Especialidad, id=self.kwargs.get("especialidad_id")
        )
        context["dias_calendario"] = DIAS_CALENDARIO
        return context


DIAS_CALENDARIO = 15

NOMBRES_DIAS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
NOMBRES_MESES_ES = [
    "",
    "Ene",
    "Feb",
    "Mar",
    "Abr",
    "May",
    "Jun",
    "Jul",
    "Ago",
    "Sep",
    "Oct",
    "Nov",
    "Dic",
]


class TurnosDisponiblesView(PerfilPacienteRequiredMixin, TemplateView):
    """Paso 3: calendario de 15 días o lista de horarios según si hay fecha seleccionada.

    Sin fecha en GET: muestra el calendario con los días que tienen turnos libres.
    Con fecha en GET: muestra los horarios disponibles de ese día, filtrando pasados.
    """

    template_name = "clinica/turnos_disponibles.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        medico = get_object_or_404(Medico, id=self.kwargs.get("medico_id"))
        hoy = timezone.localdate()
        ahora = timezone.now()

        fecha_str = self.request.GET.get("fecha")
        fecha_elegida = None

        if fecha_str:
            try:
                parsed = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                if hoy <= parsed <= hoy + timedelta(days=DIAS_CALENDARIO):
                    fecha_elegida = parsed
            except ValueError:
                pass

        context["medico"] = medico

        if fecha_elegida:
            # Mostrar horarios del día elegido, filtrando slots pasados
            slots = slots_libres_de_medico(medico, fecha_elegida)
            slots_futuros = [s for s in slots if s > ahora]
            context["modo"] = "horarios"
            context["fecha"] = fecha_elegida
            context["fecha_str"] = fecha_elegida.strftime("%Y-%m-%d")
            context["turnos"] = [
                {"hora": s.strftime("%H:%M"), "datetime": s} for s in slots_futuros
            ]
        else:
            # Mostrar calendario: calcular cuáles días tienen turnos disponibles
            dias = []
            for i in range(DIAS_CALENDARIO + 1):
                dia = hoy + timedelta(days=i)
                slots = slots_libres_de_medico(medico, dia)
                # Para hoy, solo slots futuros
                if dia == hoy:
                    slots = [s for s in slots if s > ahora]
                dias.append(
                    {
                        "fecha": dia,
                        "fecha_str": dia.strftime("%Y-%m-%d"),
                        "nombre_dia": f"{NOMBRES_DIAS_ES[dia.weekday()]} {dia.day:02d}/{dia.month:02d}",
                        "disponible": len(slots) > 0,
                        "cantidad": len(slots),
                    }
                )
            context["modo"] = "calendario"
            context["dias"] = dias
            context["hoy"] = hoy

        return context


class ConfirmarTurnoView(PerfilPacienteRequiredMixin, CreateView):
    """Paso 4: confirma y crea el turno.

    El chequeo de 'usuario sin perfil de paciente' lo hace
    PerfilPacienteRequiredMixin (en main), no este método.
    """

    model = Turno
    template_name = "clinica/confirmar_turno.html"
    fields = ["motivo", "observaciones"]
    success_url = reverse_lazy("app:lista_turnos")

    def _fecha_hora(self):
        naive = datetime.strptime(
            f"{self.kwargs['fecha']} {self.kwargs['hora']}", "%Y-%m-%d %H:%M"
        )
        return timezone.make_aware(naive)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["medico"] = get_object_or_404(Medico, id=self.kwargs.get("medico_id"))
        context["fecha_hora"] = self._fecha_hora()
        context["es_admin"] = self.request.user.is_staff
        if self.request.user.is_staff:
            context["pacientes"] = Paciente.objects.all().order_by("apellido", "nombre")
        else:
            context["paciente"] = Paciente.objects.get(usuario=self.request.user)
        return context

    def form_valid(self, form):
        medico = get_object_or_404(Medico, id=self.kwargs.get("medico_id"))

        if self.request.user.is_staff:
            paciente_id = self.request.POST.get("paciente_id")
            if not paciente_id:
                form.add_error(None, "Debés seleccionar un paciente de la lista.")
                return self.form_invalid(form)
            paciente = get_object_or_404(Paciente, id=paciente_id)
        else:
            paciente = Paciente.objects.get(usuario=self.request.user)

        turno, errors = Turno.new(
            medico=medico,
            paciente=paciente,
            fecha_hora=self._fecha_hora(),
            motivo=form.cleaned_data["motivo"],
            observaciones=form.cleaned_data.get("observaciones", ""),
            creado_por=self.request.user,
        )
        if errors:
            for error in errors:
                form.add_error(None, error)
            return self.form_invalid(form)

        messages.success(
            self.request,
            f"Turno solicitado con {medico} para el "
            f"{self._fecha_hora():%d/%m/%Y %H:%M}.",
        )
        return redirect(self.success_url)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class AceptarTurnoView(LoginRequiredMixin, View):
    """El médico asignado (o staff) confirma un turno pendiente. Solo POST."""

    def post(self, request, pk):
        turno = get_object_or_404(Turno, pk=pk)
        if not (request.user.is_staff or turno.medico.usuario_id == request.user.id):
            messages.error(request, "Solo el médico asignado puede aceptar este turno.")
            return redirect("app:lista_turnos")
        if turno.estado != Turno.PENDIENTE:
            messages.error(request, "Solo se pueden aceptar turnos pendientes.")
            return redirect("app:lista_turnos")
        turno.aceptar()
        messages.success(request, "Turno aceptado.")
        return redirect("app:lista_turnos")


class RechazarTurnoView(LoginRequiredMixin, View):
    """El médico asignado (o staff) rechaza un turno pendiente. Solo POST.

    Reutiliza la transición a 'cancelado' (Turno.rechazar()).
    """

    def post(self, request, pk):
        turno = get_object_or_404(Turno, pk=pk)
        if not (request.user.is_staff or turno.medico.usuario_id == request.user.id):
            messages.error(
                request, "Solo el médico asignado puede rechazar este turno."
            )
            return redirect("app:lista_turnos")
        if turno.estado != Turno.PENDIENTE:
            messages.error(request, "Solo se pueden rechazar turnos pendientes.")
            return redirect("app:lista_turnos")
        turno.rechazar()
        messages.success(request, "Turno rechazado.")
        return redirect("app:lista_turnos")


class CancelarTurnoView(LoginRequiredMixin, TemplateView):
    """El paciente (o staff) cancela un turno. GET confirma, POST cancela."""

    template_name = "clinica/confirmar_cancelacion.html"

    def _turno_si_permitido(self, request, pk):
        turno = get_object_or_404(Turno, pk=pk)
        es_paciente = Paciente.objects.filter(
            usuario=request.user, pk=turno.paciente_id
        ).exists()
        if not (request.user.is_staff or es_paciente):
            return None
        return turno

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["turno"] = get_object_or_404(Turno, pk=self.kwargs["pk"])
        return context

    def get(self, request, *args, **kwargs):
        turno = self._turno_si_permitido(request, kwargs["pk"])
        if turno is None:
            messages.error(request, "No podés cancelar este turno.")
            return redirect("app:lista_turnos")
        if turno.estado in [Turno.CANCELADO, Turno.ATENDIDO, Turno.NO_ASISTIO]:
            messages.error(request, "Este turno no se puede cancelar.")
            return redirect("app:lista_turnos")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        turno = self._turno_si_permitido(request, kwargs["pk"])
        if turno is None:
            messages.error(request, "No podés cancelar este turno.")
            return redirect("app:lista_turnos")
        if turno.estado in [Turno.CANCELADO, Turno.ATENDIDO, Turno.NO_ASISTIO]:
            messages.error(request, "Este turno no se puede cancelar.")
            return redirect("app:lista_turnos")
        turno.cancelar()
        messages.success(request, "Turno cancelado.")
        return redirect("app:lista_turnos")
        
    
    
class RegistrarAsistenciaView(LoginRequiredMixin, View):
    """Permite al médico o staff registrar si el paciente asistió o no.
    SOLO para turnos con fecha_hora <= hoy (mismo día o anterior).
    """

    def post(self, request, pk):
        turno = get_object_or_404(Turno, pk=pk)
        asistio = request.POST.get('asistio') == 'true'
        
        # Verificar permisos: solo el médico asignado o staff
        if not (request.user.is_staff or turno.medico.usuario_id == request.user.id):
            messages.error(request, "No tenés permiso para registrar asistencia de este turno.")
            return redirect('app:lista_turnos')
        
        # 👇 VALIDACIÓN: Solo se puede marcar si la fecha ya pasó o es hoy
        hoy = timezone.now().date()
        fecha_turno = turno.fecha_hora.date()
        
        if fecha_turno > hoy:
            messages.error(request, "No se puede registrar asistencia para turnos futuros.")
            return redirect('app:lista_turnos')
        
        # Solo se puede marcar si el turno está confirmado
        if turno.estado != Turno.CONFIRMADO:
            messages.error(request, "Solo se puede registrar asistencia para turnos confirmados.")
            return redirect('app:lista_turnos')
        
        # Marcar asistencia
        turno.marcar_asistencia(asistio)
        
        if asistio:
            messages.success(request, "Turno marcado como atendido.")
        else:
            messages.success(request, "Turno marcado como no asistió.")
        
        return redirect('app:lista_turnos')