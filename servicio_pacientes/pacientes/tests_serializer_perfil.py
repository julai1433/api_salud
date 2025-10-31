from django.test import TestCase
from pacientes.models import Paciente
from pacientes.serializers import PacientePerfilUpdateSerializer

class PacientePerfilUpdateSerializerTests(TestCase):
    def setUp(self):
        self.paciente = Paciente.objects.create(
            nombre="Ana",
            fecha_nacimiento="1990-05-20",
            nss="01234567890",
            email="ana@example.com",
            password="secreto",
        )
        self.otro = Paciente.objects.create(
            nombre="Luis",
            fecha_nacimiento="1988-01-02",
            nss="11111111111",
            email="luis@example.com",
            password="x",
        )

    def test_actualiza_nombre_parcial_ok(self):
        from pacientes.serializers import PacientePerfilUpdateSerializer
        s = PacientePerfilUpdateSerializer(instance=self.paciente, data={"nombre": "Ana López"}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)
        obj = s.save()
        self.assertEqual(obj.nombre, "Ana López")

    def test_rechaza_es_doctor_en_payload(self):
        from pacientes.serializers import PacientePerfilUpdateSerializer
        s = PacientePerfilUpdateSerializer(instance=self.paciente, data={"es_doctor": True}, partial=True)
        self.assertFalse(s.is_valid())
        self.assertIn("es_doctor", s.errors)

    def test_email_duplicado(self):
        from pacientes.serializers import PacientePerfilUpdateSerializer
        s = PacientePerfilUpdateSerializer(instance=self.paciente, data={"email": "luis@example.com"}, partial=True)
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

    def test_nss_inmutable(self):
        from pacientes.serializers import PacientePerfilUpdateSerializer
        s = PacientePerfilUpdateSerializer(instance=self.paciente, data={"nss": "99999999999"}, partial=True)
        self.assertFalse(s.is_valid())
        self.assertIn("nss", s.errors)

