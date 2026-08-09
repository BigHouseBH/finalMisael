from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from .models.recordatorios import Recordatorio

# 1. Lista de recordatorios (solo pacientes)
class ListaRecordatoriosView(LoginRequiredMixin, ListView):
    model = Recordatorio
    template_name = 'clinica/recordatorios.html'
    context_object_name = 'recordatorios'

    def get_queryset(self):
        if self.request.user.is_staff:
            return Recordatorio.objects.none()
        return Recordatorio.objects.filter(
                paciente=self.request.user.paciente
            ).order_by('-fecha_creacion')  # El '-' ordena de más nuevo a más viejo


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_staff:
            messages.warning(self.request, "Los administradores no tienen recordatorios.")
        return context

# 2. Crear recordatorio (solo pacientes)
class CrearRecordatorioView(LoginRequiredMixin, CreateView):
    model = Recordatorio
    fields = ['titulo', 'descripcion', 'fecha_recordatorio']
    template_name = 'clinica/crear_recordatorio.html'
    success_url = reverse_lazy('app:lista_recordatorios')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_staff:
            messages.error(request, "No puedes crear recordatorios como administrador.")
            return redirect('app:home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.paciente = self.request.user.paciente
        messages.success(self.request, "Recordatorio creado exitosamente.")
        return super().form_valid(form)

# 3. Marcar recordatorio como leído (solo pacientes)
class MarcarLeidoView(LoginRequiredMixin, UpdateView):
    model = Recordatorio
    fields = []  # No se edita ningún campo directamente
    success_url = reverse_lazy('app:recordatorios')

    def get_queryset(self):
        # Solo permite modificar recordatorios del paciente autenticado
        return Recordatorio.objects.filter(paciente=self.request.user.paciente)

    def form_valid(self, form):
        form.instance.leido = True
        messages.success(self.request, "Recordatorio marcado como leído.")
        return super().form_valid(form)