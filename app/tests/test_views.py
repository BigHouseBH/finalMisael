from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Especialidad, Medico, ObraSocial, Paciente, Turno
from app.models.recordatorios import Recordatorio


class ViewAccessTest(TestCase):
    def setUp(self):
        self.especialidad = Especialidad.objects.create(
            nombre="Clínica Médica", descripcion="General"
        )
        self.medico = Medico.objects.create(
            nombre="Ana",
            apellido="Suarez",
            matricula="MP-1000",
            especialidad=self.especialidad,
        )

    def test_home_es_publica(self):
        response = self.client.get(reverse("app:home"))
        self.assertEqual(response.status_code, 200)

    def test_lista_medicos_es_publica(self):
        response = self.client.get(reverse("app:lista_medicos"))
        self.assertEqual(response.status_code, 200)

    def test_turnos_requiere_login(self):
        response = self.client.get(reverse("app:lista_turnos"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_detalle_medico_requiere_login(self):
        response = self.client.get(reverse("app:detalle_medico", args=[self.medico.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


class TurnosPorRolViewTest(TestCase):
    def setUp(self):
        self.obra_social = ObraSocial.objects.create(nombre="OSDE")
        self.especialidad = Especialidad.objects.create(
            nombre="Cardiología", descripcion="Corazón"
        )

        self.admin = User.objects.create_superuser(
            username="admin_test", email="admin@test.com", password="1234"
        )

        self.paciente_user = User.objects.create_user(
            username="paciente1", email="pac1@test.com", password="1234"
        )
        self.paciente = Paciente.objects.create(
            usuario=self.paciente_user,
            nombre="Juan",
            apellido="Pérez",
            email="pac1@test.com",
            telefono="123456",
            dni="11111111",
            obra_social=self.obra_social,
        )

        self.otro_user = User.objects.create_user(
            username="paciente2", email="pac2@test.com", password="1234"
        )
        self.otro_paciente = Paciente.objects.create(
            usuario=self.otro_user,
            nombre="María",
            apellido="Gómez",
            email="pac2@test.com",
            telefono="654321",
            dni="22222222",
            obra_social=self.obra_social,
        )

        self.medico_user = User.objects.create_user(
            username="medico1", email="med@test.com", password="1234"
        )
        self.medico = Medico.objects.create(
            usuario=self.medico_user,
            nombre="Laura",
            apellido="Romero",
            matricula="MP-9999",
            especialidad=self.especialidad,
        )

        self.otro_medico = Medico.objects.create(
            nombre="Carlos",
            apellido="López",
            matricula="MP-8888",
            especialidad=self.especialidad,
        )

        self.turno_paciente, _ = Turno.new(
            medico=self.medico,
            paciente=self.paciente,
            fecha_hora=timezone.now() + timedelta(days=1),
            motivo="Control",
            creado_por=self.paciente_user,
        )
        self.turno_otro, _ = Turno.new(
            medico=self.medico,
            paciente=self.otro_paciente,
            fecha_hora=timezone.now() + timedelta(days=2),
            motivo="Consulta",
            creado_por=self.otro_user,
        )
        self.turno_otro_medico, _ = Turno.new(
            medico=self.otro_medico,
            paciente=self.otro_paciente,
            fecha_hora=timezone.now() + timedelta(days=3),
            motivo="Chequeo",
            creado_por=self.otro_user,
        )

    def test_paciente_ve_solo_sus_turnos(self):
        self.client.login(username="paciente1", password="1234")
        response = self.client.get(reverse("app:lista_turnos"))
        turnos = list(response.context["turnos"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(turnos), 1)
        self.assertEqual(turnos[0].pk, self.turno_paciente.pk)

    def test_medico_ve_solo_sus_turnos_asignados(self):
        self.client.login(username="medico1", password="1234")
        response = self.client.get(reverse("app:lista_turnos"))
        turnos = list(response.context["turnos"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {t.pk for t in turnos}, {self.turno_paciente.pk, self.turno_otro.pk}
        )

    def test_admin_ve_todos_los_turnos(self):
        self.client.login(username="admin_test", password="1234")
        response = self.client.get(reverse("app:lista_turnos"))
        turnos = list(response.context["turnos"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {t.pk for t in turnos},
            {self.turno_paciente.pk, self.turno_otro.pk, self.turno_otro_medico.pk},
        )

    def test_paciente_en_lista_turnos_ve_cancelar_y_no_ve_acciones_de_medico(self):
        self.client.login(username="paciente1", password="1234")
        response = self.client.get(reverse("app:lista_turnos"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cancelar")
        self.assertNotContains(
            response, reverse("app:aceptar_turno", args=[self.turno_paciente.pk])
        )
        self.assertNotContains(
            response, reverse("app:rechazar_turno", args=[self.turno_paciente.pk])
        )
        self.assertNotContains(
            response, reverse("app:historial", args=[self.paciente.pk])
        )

    def test_medico_en_lista_turnos_ve_acciones_post_de_aceptar_rechazar(self):
        self.client.login(username="medico1", password="1234")
        response = self.client.get(reverse("app:lista_turnos"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, reverse("app:aceptar_turno", args=[self.turno_paciente.pk])
        )
        self.assertContains(
            response, reverse("app:rechazar_turno", args=[self.turno_paciente.pk])
        )
        self.assertContains(
            response, reverse("app:historial", args=[self.paciente.pk])
        )

    def test_paciente_no_puede_ver_lista_global_de_pacientes(self):
        self.client.login(username="paciente1", password="1234")
        response = self.client.get(reverse("app:lista_pacientes"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("app:home"))

    def test_admin_puede_ver_lista_global_de_pacientes(self):
        self.client.login(username="admin_test", password="1234")
        response = self.client.get(reverse("app:lista_pacientes"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Juan")
        self.assertContains(response, "María")

    def test_medico_asignado_puede_aceptar_turno_pendiente(self):
        self.client.login(username="medico1", password="1234")
        response = self.client.post(
            reverse("app:aceptar_turno", args=[self.turno_paciente.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.turno_paciente.refresh_from_db()
        self.assertEqual(self.turno_paciente.estado, Turno.CONFIRMADO)

    def test_usuario_ajeno_no_puede_aceptar_turno(self):
        self.client.login(username="paciente2", password="1234")
        response = self.client.post(
            reverse("app:aceptar_turno", args=[self.turno_paciente.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.turno_paciente.refresh_from_db()
        self.assertEqual(self.turno_paciente.estado, Turno.PENDIENTE)

    def test_medico_asignado_puede_rechazar_turno(self):
        self.client.login(username="medico1", password="1234")
        response = self.client.post(
            reverse("app:rechazar_turno", args=[self.turno_paciente.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.turno_paciente.refresh_from_db()
        self.assertEqual(self.turno_paciente.estado, Turno.CANCELADO)

    def test_paciente_puede_cancelar_turno_propio(self):
        self.client.login(username="paciente1", password="1234")
        response = self.client.post(
            reverse("app:cancelar_turno", args=[self.turno_paciente.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.turno_paciente.refresh_from_db()
        self.assertEqual(self.turno_paciente.estado, Turno.CANCELADO)

    def test_paciente_no_puede_cancelar_turno_ajeno(self):
        self.client.login(username="paciente2", password="1234")
        response = self.client.post(
            reverse("app:cancelar_turno", args=[self.turno_paciente.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.turno_paciente.refresh_from_db()
        self.assertEqual(self.turno_paciente.estado, Turno.PENDIENTE)

    def test_registrar_asistencia_como_atendido(self):
        self.client.login(username="medico1", password="1234")
        # El turno debe ser de hoy y estar confirmado
        self.turno_paciente.fecha_hora = timezone.now()
        self.turno_paciente.estado = Turno.CONFIRMADO
        self.turno_paciente.save()

        response = self.client.post(
            reverse("app:registrar_asistencia", args=[self.turno_paciente.pk]),
            {"asistio": "true"},
        )
        self.assertEqual(response.status_code, 302)
        self.turno_paciente.refresh_from_db()
        self.assertEqual(self.turno_paciente.estado, Turno.ATENDIDO)

    def test_registrar_asistencia_como_no_asistio(self):
        self.client.login(username="medico1", password="1234")
        # El turno debe ser de hoy y estar confirmado
        self.turno_paciente.fecha_hora = timezone.now()
        self.turno_paciente.estado = Turno.CONFIRMADO
        self.turno_paciente.save()

        response = self.client.post(
            reverse("app:registrar_asistencia", args=[self.turno_paciente.pk]),
            {"asistio": "false"},
        )
        self.assertEqual(response.status_code, 302)
        self.turno_paciente.refresh_from_db()
        self.assertEqual(self.turno_paciente.estado, Turno.NO_ASISTIO)

    def test_confirmar_turno_crea_turno_exitosamente(self):
        self.client.login(username="paciente1", password="1234")
        fecha_str = "2026-11-20"
        hora_str = "10:00"
        response = self.client.post(
            reverse(
                "app:confirmar_turno",
                kwargs={
                    "medico_id": self.medico.pk,
                    "fecha": fecha_str,
                    "hora": hora_str,
                },
            ),
            {"motivo": "Dolor de cabeza", "observaciones": "Primera vez"},
        )
        self.assertEqual(response.status_code, 302)
        nuevo_turno = Turno.objects.filter(
            paciente=self.paciente,
            medico=self.medico,
            motivo="Dolor de cabeza",
        ).first()
        self.assertIsNotNone(nuevo_turno)
        self.assertEqual(nuevo_turno.estado, Turno.PENDIENTE)

    def test_lista_recordatorios_paciente(self):
        self.client.login(username="paciente1", password="1234")
        recordatorio = Recordatorio.objects.create(
            turno=self.turno_paciente,
            paciente=self.paciente,
            mensaje="Recordatorio para paciente 1",
        )
        response = self.client.get(reverse("app:recordatorios"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, recordatorio.mensaje)
