# app/views_historial.py
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Paciente, Turno

class HistorialView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Vista para mostrar el historial de turnos de un paciente.
    Solo accesible para médicos y staff.
    """
    model = Paciente
    template_name = 'clinica/historial.html'
    context_object_name = 'paciente'

    def test_func(self):
        """Verifica que el usuario sea médico o staff."""
        return hasattr(self.request.user, 'medico') or self.request.user.is_staff

    def get_context_data(self, **kwargs):
        """Agrega los turnos del paciente al contexto."""
        context = super().get_context_data(**kwargs)
        
        # Obtener todos los turnos del paciente ordenados por fecha descendente
        context['turnos'] = Turno.objects.filter(
            paciente=self.object
        ).select_related('medico', 'medico__usuario').order_by('-fecha_hora')
        
        return context