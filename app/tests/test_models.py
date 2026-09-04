"""Pruebas unitarias de los modelos."""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, time, timedelta

# Importamos cada modelo de su archivo correspondiente
from app.models.especialidad import Especialidad
from app.models.medico import Medico
from app.models.franja_horaria import FranjaHoraria
from app.models.obra_social import ObraSocial
from app.models.paciente import Paciente
from app.models.turno import Turno
from app.models.ausencia import Ausencia
from app.models.recordatorios import Recordatorio


class EspecialidadModelTest(TestCase):
    """Verifica comportamiento basico y validaciones del modelo Especialidad."""

    def setUp(self):
        self.especialidad = Especialidad.objects.create(
            nombre="Pediatría",
            descripcion="Atención médica infantil",
        )

    def test_str_retorna_nombre(self):
        self.assertEqual(str(self.especialidad), "Pediatría")

    def test_validate_datos_correctos_retorna_lista_vacia(self):
        errors = Especialidad.validate("Cardiología", "Especialidad del corazón")
        self.assertEqual(errors, [])

    def test_validate_nombre_vacio_retorna_error(self):
        errors = Especialidad.validate("", "Especialidad sin nombre")
        self.assertTrue(len(errors) > 0)

    def test_new_crea_especialidad_con_datos_validos(self):
        especialidad, errors = Especialidad.new("Clínica Médica", "Atención integral")
        self.assertEqual(errors, [])
        self.assertIsNotNone(especialidad)
        self.assertEqual(especialidad.nombre, "Clínica Médica")
        self.assertTrue(Especialidad.objects.filter(nombre="Clínica Médica").exists())

    def test_new_con_datos_invalidos_retorna_errores_y_no_crea(self):
        count_antes = Especialidad.objects.count()
        especialidad, errors = Especialidad.new("", "")
        self.assertIsNone(especialidad)
        self.assertTrue(len(errors) > 0)
        self.assertEqual(Especialidad.objects.count(), count_antes)

    def test_update_modifica_datos_correctamente(self):
        errors = self.especialidad.update("Neurología", "Sistema nervioso")
        self.assertEqual(errors, [])
        self.especialidad.refresh_from_db()
        self.assertEqual(self.especialidad.nombre, "Neurología")
        self.assertEqual(self.especialidad.descripcion, "Sistema nervioso")

    def test_update_con_datos_invalidos_no_modifica(self):
        errors = self.especialidad.update("", "")
        self.assertTrue(len(errors) > 0)
        self.especialidad.refresh_from_db()
        self.assertEqual(self.especialidad.nombre, "Pediatría")


class MedicoModelTest(TestCase):
    """Verifica comportamiento básico y validaciones del modelo Medico."""

    def setUp(self):
        self.especialidad = Especialidad.objects.create(
            nombre="Pediatría",
            descripcion="Atención médica infantil",
        )
        self.medico = Medico.objects.create(
            nombre="Laura",
            apellido="Romero",
            matricula="MP-9999",
            especialidad=self.especialidad,
        )

    def test_str_incluye_apellido_y_nombre(self):
        self.assertIn("Romero", str(self.medico))
        self.assertIn("Laura", str(self.medico))

    def test_nombre_completo(self):
        self.assertEqual(self.medico.nombre_completo(), "Laura Romero")

    def test_cantidad_turnos_inicial_es_cero(self):
        self.assertEqual(self.medico.cantidad_turnos(), 0)

    def test_validate_datos_correctos_retorna_lista_vacia(self):
        errors = Medico.validate("Ana", "García", "MP-0001", self.especialidad)
        self.assertEqual(errors, [])

    def test_new_crea_medico_con_datos_validos(self):
        medico, errors = Medico.new("Carlos", "López", "MP-1234", self.especialidad)
        self.assertEqual(errors, [])
        self.assertIsNotNone(medico)
        self.assertEqual(medico.apellido, "López")

    def test_new_con_obras_sociales_asigna_correctamente(self):
        obra = ObraSocial.objects.create(nombre="OSDE")
        medico, errors = Medico.new("Juan", "Perez", "MP-5555", self.especialidad, obras_sociales=[obra])
        self.assertEqual(errors, [])
        self.assertIn(obra, medico.obras_sociales.all())
    
    def test_update_actualiza_obras_sociales(self):
        obra1 = ObraSocial.objects.create(nombre="OSDE")
        obra2 = ObraSocial.objects.create(nombre="Swiss Medical")
        self.medico.update("Laura", "Romero", "MP-9999", self.especialidad, obras_sociales=[obra1])
        self.medico.refresh_from_db()
        self.assertIn(obra1, self.medico.obras_sociales.all())
        
        self.medico.update("Laura", "Romero", "MP-9999", self.especialidad, obras_sociales=[obra2])
        self.medico.refresh_from_db()
        self.assertNotIn(obra1, self.medico.obras_sociales.all())
        self.assertIn(obra2, self.medico.obras_sociales.all())
    
class PacienteModelTest(TestCase):
    """Verifica comportamiento básico y validaciones del modelo Paciente."""

    def setUp(self):
        #Obra social base
        self.obra_social = ObraSocial.objects.create(nombre="IOMA")
    
        #Usuario base
        self.user = User.objects.create_user(username='maxi', password='1234')
    
        #Crea paciente base con metodo new
        self.paciente, errors = Paciente.new(
            usuario=self.user,
            nombre="Juan",
            apellido="Perez",
            email="juan@perez.com",
            telefono="123456",
            dni="11111111",
            obra_social=self.obra_social
        )
         
    #Metodos y formato str

    def test_str_formato_correcto(self):
        #Verifica formato exacto: Apellido, Nombre
        self.assertEqual(str(self.paciente), "Perez, Juan")

    def test_puede_solicitar_turno_true(self):
        #Caso ideal con datos completos
        self.assertTrue(self.paciente.puede_solicitar_turno())

    def test_puede_solicitar_turno_false_sin_obra_social(self):
        #Caso negativo sin obra social
        self.paciente.obra_social = None
        self.assertFalse(self.paciente.puede_solicitar_turno())

    def test_puede_solicitar_turno_false_sin_nada(self):
        #Caso negativo sin telefono ni obra social
        self.paciente.telefono = ""
        self.paciente.obra_social = None
        self.assertFalse(self.paciente.puede_solicitar_turno())

    def test_puede_solicitar_turno_false_sin_telefono(self):
        #Caso borde sin telefono
        self.paciente.telefono = ""
        self.assertFalse(self.paciente.puede_solicitar_turno())

    #Validaciones

    def test_validate_datos_correctos_retorna_lista_vacia(self):
        #Valida datos completos y correctos
        errors = Paciente.validate("Juan", "Perez", "12345678", "juan@test.com", "123456", self.obra_social)
        self.assertEqual(errors, [])

    def test_validate_campos_obligatorios_vacios_retorna_errores(self):
        #Valida obligatoriedad de nombre, apellido y DNI
        errors = Paciente.validate("", "", "", "juan@test.com", "123456", self.obra_social)
        self.assertIn("El nombre es obligatorio.", errors)
        self.assertIn("El apellido es obligatorio.", errors)
        self.assertIn("El DNI es obligatorio.", errors)

    def test_validate_dni_duplicado_retorna_error(self):
        #Valida rechazo de DNI duplicado existente en setUp
        errors = Paciente.validate("Otro", "Persona", "11111111", "otro@test.com", "999", self.obra_social)
        self.assertIn("Ya existe un paciente registrado con ese DNI.", errors)

    def test_validate_email_invalido_retorna_error(self):
        #Valida formato de email
        errors = Paciente.validate("Juan", "Perez", "99999999", "email-invalido", "123456", self.obra_social)
        self.assertIn("El email ingresado no es válido.", errors)

    #Creacion new

    def test_new_crea_paciente_con_datos_validos(self):
        nuevo_user = User.objects.create_user(username="roberto")
        
        paciente, errors = Paciente.new(
            nuevo_user, "Roberto", "Rubidarte", "roberto@test.com", "654321", "46087375", self.obra_social
        )
        
        #Verifica creacion y persistencia en base de datos
        self.assertEqual(errors, [])
        self.assertIsNotNone(paciente)
        self.assertEqual(paciente.nombre, "Roberto")
        self.assertTrue(Paciente.objects.filter(dni="46087375").exists())

    def test_new_con_datos_invalidos_no_crea_paciente(self):
        count_antes = Paciente.objects.count()
        nuevo_user = User.objects.create_user(username="roberto2")

        paciente, errors = Paciente.new(
            nuevo_user, "", "", "email-invalido", "", "", None
        )

        #Verifica que rechaza creacion y no altera la base de datos
        self.assertIsNone(paciente)
        self.assertTrue(len(errors) > 0)
        self.assertEqual(Paciente.objects.count(), count_antes)

    #Actualizacion update

    def test_update_modifica_datos_correctamente(self):
        errors = self.paciente.update(
            "Roberto Actualizado", 
            "Rubidarte", 
            "nuevo_email@test.com", 
            "999999", 
            "46087375", 
            self.obra_social
        )
        
        #Verifica actualizacion y persistencia de cambios
        self.assertEqual(errors, [])
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.nombre, "Roberto Actualizado")
        self.assertEqual(self.paciente.email, "nuevo_email@test.com")

    def test_update_con_datos_invalidos_no_modifica(self):
        nombre_original = self.paciente.nombre
        errors = self.paciente.update("", "", "email-invalido", "", "", None)

        #Verifica que detecta error y mantiene valores originales
        self.assertTrue(len(errors) > 0)
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.nombre, nombre_original)

    def test_update_con_dni_de_otro_paciente_retorna_error(self):
        nuevo_user = User.objects.create_user(username="joaco")
        Paciente.new(
            nuevo_user, "joaco", "Rubidarte", "joaco@test.com", "654321", "12345678", self.obra_social
        )

        #Verifica rechazo de actualizacion por DNI duplicado
        errors = self.paciente.update(
            "Juan", "Perez", "juan@perez.com", "123456", "12345678", self.obra_social 
        )
        self.assertTrue(len(errors) > 0)

class AusenciaModelTest(TestCase):

        def setUp(self):
          self.especialidad = Especialidad.objects.create(nombre="Pediatría")
          self.medico = Medico.objects.create(
              nombre="Laura", apellido="Romero",
              matricula="MP-9999", especialidad=self.especialidad
          ) 

        def test_validate_fecha_fin_menor_a_inicio_retorna_error(self):
          from datetime import date
          errors = Ausencia.validate("Vacaciones", date(2025, 6, 10), date(2025, 6, 1), )
          self.assertTrue(len(errors) > 0)

    #-------------------new-------------------

        def test_new_crea_ausencia_con_datos_validos(self):
            ausencia, errors = Ausencia.new("Vacaciones", date(2025, 6, 1), date(2025, 6, 10), self.medico)
            self.assertEqual(errors, [])
            self.assertIsNotNone(ausencia)
            self.assertTrue(Ausencia.objects.filter(motivo="Vacaciones").exists())

        def test_new_con_datos_invalidos_no_crea(self):
            count_antes = Ausencia.objects.count()
            ausencia, errors = Ausencia.new("", None, None, self.medico)
            self.assertIsNone(ausencia)
            self.assertTrue(len(errors) > 0)
            self.assertEqual(Ausencia.objects.count(), count_antes)

        #-------------------update-------------------

        def test_update_modifica_motivo_correctamente(self):
            ausencia, _ = Ausencia.new("Vacaciones", date(2025, 6, 1), date(2025, 6, 10), self.medico)
            errors = ausencia.update("Congreso médico", date(2025, 6, 1), date(2025, 6, 10))
            self.assertEqual(errors, [])
            ausencia.refresh_from_db()
            self.assertEqual(ausencia.motivo, "Congreso médico")

        def test_update_con_datos_invalidos_no_modifica(self):
            ausencia, _ = Ausencia.new("Vacaciones", date(2025, 6, 1), date(2025, 6, 10), self.medico)
            errors = ausencia.update("", None, None)
            self.assertTrue(len(errors) > 0)
            ausencia.refresh_from_db()
            self.assertEqual(ausencia.motivo, "Vacaciones")

class TurnoModelTest(TestCase):

      def setUp(self):
          self.especialidad = Especialidad.objects.create(nombre="Pediatría")
          self.medico = Medico.objects.create(
              nombre="Laura", apellido="Romero",
              matricula="MP-9999", especialidad=self.especialidad
          )
          self.obra_social = ObraSocial.objects.create(nombre="IOMA")
          self.user = User.objects.create_user(username="pac_turno", password="1234")
          self.paciente, _ = Paciente.new(
              usuario=self.user,
              nombre="Misael",
              apellido="Casagrande",
              email="misael@casagrande.com",
              telefono="123456",
              dni="22222222",
              obra_social=self.obra_social,
          )
          self.fecha_valida = timezone.now() + timedelta(days=5)

      #-------------------validate-------------------

      def test_validate_datos_correctos_retorna_lista_vacia(self):
          errors = Turno.validate(self.medico, self.paciente, self.fecha_valida, "Consulta")
          self.assertEqual(errors, [])

      def test_validate_sin_medico_retorna_error(self):
          errors = Turno.validate(None, self.paciente, self.fecha_valida, "Consulta")
          self.assertTrue(len(errors) > 0)

      def test_validate_sin_paciente_retorna_error(self):
          errors = Turno.validate(self.medico, None, self.fecha_valida, "Consulta")
          self.assertTrue(len(errors) > 0)

      def test_validate_sin_motivo_retorna_error(self):
          errors = Turno.validate(self.medico, self.paciente, self.fecha_valida, "")
          self.assertTrue(len(errors) > 0)

      def test_validate_turno_duplicado_retorna_error(self):
          Turno.new(self.medico, self.paciente, self.fecha_valida, "Consulta")
          errors = Turno.validate(self.medico, self.paciente, self.fecha_valida, "Otra")
          self.assertTrue(len(errors) > 0)

      #-------------------new-------------------

      def test_new_crea_turno_con_datos_validos(self):
          turno, errors = Turno.new(self.medico, self.paciente, self.fecha_valida, "Consulta")
          self.assertEqual(errors, [])
          self.assertIsNotNone(turno)
          self.assertEqual(turno.estado, Turno.PENDIENTE)
          self.assertTrue(Turno.objects.filter(paciente=self.paciente).exists())

      def test_new_con_datos_invalidos_no_crea(self):
          count_antes = Turno.objects.count()
          turno, errors = Turno.new(None, None, None, "")
          self.assertIsNone(turno)
          self.assertTrue(len(errors) > 0)
          self.assertEqual(Turno.objects.count(), count_antes)

      #-------------------update-------------------

      def test_update_modifica_observaciones_correctamente(self):
          turno, _ = Turno.new(self.medico, self.paciente, self.fecha_valida, "Consulta")
          nueva_fecha = timezone.now() + timedelta(days=10)
          errors = turno.update(
              self.medico, self.paciente, nueva_fecha, "Consulta",
              observaciones="Nueva observación",
          )
          self.assertEqual(errors, [])
          turno.refresh_from_db()
          self.assertEqual(turno.observaciones, "Nueva observación")

      #-------------------transiciones de estado-------------------

      #Aceptacion de turno
      def test_aceptar_cambia_estado_a_confirmado(self):
          turno, _ = Turno.new(self.medico, self.paciente, self.fecha_valida, "Consulta")
          turno.aceptar()
          turno.refresh_from_db()
          self.assertEqual(turno.estado, Turno.CONFIRMADO)

      #Rechazo de turno por parte del medico
      def test_rechazar_cambia_estado_a_cancelado(self):
          turno, _ = Turno.new(self.medico, self.paciente, self.fecha_valida, "Consulta")
          turno.rechazar()
          turno.refresh_from_db()
          self.assertEqual(turno.estado, Turno.CANCELADO)

      #Cancelacion de turno por parte del paciente
      def test_cancelar_cambia_estado_a_cancelado(self):
          turno, _ = Turno.new(self.medico, self.paciente, self.fecha_valida, "Consulta")
          turno.cancelar()
          turno.refresh_from_db()
          self.assertEqual(turno.estado, Turno.CANCELADO)

      #Estado de asistencia
      def test_atendido_cambia_estado_a_atendido(self):
          turno, _ = Turno.new(self.medico, self.paciente, self.fecha_valida, "Consulta")
          turno.marcar_asistencia(True)
          turno.refresh_from_db()
          self.assertEqual(turno.estado, Turno.ATENDIDO)

      def test_no_asistio_cambia_estado_a_no_asistio(self):
          turno, _ = Turno.new(self.medico, self.paciente, self.fecha_valida, "Consulta")
          turno.marcar_asistencia(False)
          turno.refresh_from_db()
          self.assertEqual(turno.estado, Turno.NO_ASISTIO)

class FranjaHorariaModelTest(TestCase):
    """Verifica validaciones y métodos de FranjaHoraria."""

    def setUp(self):
        self.especialidad = Especialidad.objects.create(nombre="Clínica")
        self.medico = Medico.objects.create(
            nombre="Ana", apellido="García",
            matricula="MP-7777", especialidad=self.especialidad,
        )

    def test_validate_datos_correctos_retorna_lista_vacia(self):
        errors = FranjaHoraria.validate(
            self.medico, FranjaHoraria.LUNES, time(9, 0), time(17, 0)
        )
        self.assertEqual(errors, [])

    def test_validate_sin_medico_retorna_error(self):
        errors = FranjaHoraria.validate(
            None, FranjaHoraria.LUNES, time(9, 0), time(17, 0)
        )
        self.assertTrue(len(errors) > 0)

    def test_validate_hora_fin_menor_o_igual_a_inicio_retorna_error(self):
        errors = FranjaHoraria.validate(
            self.medico, FranjaHoraria.LUNES, time(17, 0), time(9, 0)
        )
        self.assertTrue(len(errors) > 0)

    def test_validate_dia_invalido_retorna_error(self):
        errors = FranjaHoraria.validate(self.medico, 99, time(9, 0), time(17, 0))
        self.assertTrue(len(errors) > 0)

    def test_new_crea_franja_con_datos_validos(self):
        franja, errors = FranjaHoraria.new(
            self.medico, FranjaHoraria.MARTES, time(8, 0), time(12, 0)
        )
        self.assertEqual(errors, [])
        self.assertIsNotNone(franja)
        self.assertTrue(self.medico.franjas.filter(dia_semana=FranjaHoraria.MARTES).exists())

    def test_new_con_datos_invalidos_no_crea(self):
        count_antes = FranjaHoraria.objects.count()
        franja, errors = FranjaHoraria.new(self.medico, FranjaHoraria.LUNES, time(17, 0), time(9, 0))
        self.assertIsNone(franja)
        self.assertTrue(len(errors) > 0)
        self.assertEqual(FranjaHoraria.objects.count(), count_antes)

    def test_update_modifica_horario_correctamente(self):
        franja, _ = FranjaHoraria.new(
            self.medico, FranjaHoraria.MIERCOLES, time(9, 0), time(13, 0)
        )
        errors = franja.update(
            self.medico, FranjaHoraria.MIERCOLES, time(14, 0), time(18, 0)
        )
        self.assertEqual(errors, [])
        franja.refresh_from_db()
        self.assertEqual(franja.hora_inicio, time(14, 0))
        self.assertEqual(franja.hora_fin, time(18, 0))


class ObraSocialModelTest(TestCase):
    """Verifica comportamiento de ObraSocial."""

    def setUp(self):
        self.obra_social = ObraSocial.objects.create(nombre="IOMA")

    def test_str_retorna_nombre(self):
        self.assertEqual(str(self.obra_social), "IOMA")

    def test_validate_nombre_vacio_retorna_error(self):
        errors = ObraSocial.validate("")
        self.assertTrue(len(errors) > 0)

    def test_validate_nombre_duplicado_retorna_error(self):
        errors = ObraSocial.validate("IOMA")
        self.assertTrue(len(errors) > 0)

    def test_new_crea_obra_social_valida(self):
        obra, errors = ObraSocial.new("OSDE")
        self.assertEqual(errors, [])
        self.assertIsNotNone(obra)

    def test_medicos_disponibles_cuenta_correctamente(self):
        especialidad = Especialidad.objects.create(nombre="Pediatría")
        medico, _ = Medico.new("Juan", "Perez", "MP-111", especialidad, obras_sociales=[self.obra_social])
        self.assertEqual(self.obra_social.medicos_disponibles, 1)

    def test_update_nombre_valido(self):
        
        # Actualizamos
        errors = self.obra_social.update(nombre="SWISS MEDICAL")
        # Verificamos
        self.assertEqual(errors, [])
        self.assertEqual(self.obra_social.nombre, "SWISS MEDICAL")
        # Confirmamos que se guardó en BD
        self.assertTrue(ObraSocial.objects.filter(nombre="SWISS MEDICAL").exists())


class RecordatorioModelTest(TestCase):
    """Verifica creación y métodos del modelo Recordatorio."""

    def setUp(self):
        self.user = User.objects.create_user(username="paciente_rec", password="password")
        self.especialidad = Especialidad.objects.create(nombre="Oftalmología")
        self.obra_social = ObraSocial.objects.create(nombre="OSDE")
        self.medico = Medico.objects.create(
            nombre="Carlos", apellido="Vargas",
            matricula="MP-5555", especialidad=self.especialidad,
        )
        self.paciente = Paciente.objects.create(
            usuario=self.user,
            nombre="Lucas", apellido="Silva",
            email="lucas@test.com", telefono="123456",
            dni="33333333", obra_social=self.obra_social,
        )
        self.turno, _ = Turno.new(
            medico=self.medico,
            paciente=self.paciente,
            fecha_hora=timezone.now() + timedelta(days=1),
            motivo="Control visual",
        )

    def test_creacion_recordatorio_por_defecto_no_leido(self):
        recordatorio = Recordatorio.objects.create(
            turno=self.turno,
            paciente=self.paciente,
            mensaje="Recordatorio: Mañana tenés tu turno con Carlos Vargas.",
        )
        self.assertFalse(recordatorio.leido)
        self.assertEqual(recordatorio.turno, self.turno)
        self.assertEqual(recordatorio.paciente, self.paciente)

    def test_str_recordatorio(self):
        recordatorio = Recordatorio.objects.create(
            turno=self.turno,
            paciente=self.paciente,
            mensaje="Tu turno es mañana",
        )
        self.assertIn(self.user.username, str(recordatorio))

    def test_marcar_como_leido(self):
        recordatorio = Recordatorio.objects.create(
            turno=self.turno,
            paciente=self.paciente,
            mensaje="Recordatorio de prueba",
        )
        recordatorio.leido = True
        recordatorio.save()
        recordatorio.refresh_from_db()
        self.assertTrue(recordatorio.leido)
