from django.test import TestCase
from pacientes.models import Paciente
from pacientes.serializers import PacienteRegistroSerializer

class PacienteRegistroSerializerTests(TestCase):
    def setUp(self):
        self.valid_payload = {
            "nombre": "Ana López",
            "fecha_nacimiento": "1990-05-20",
            "nss": "01234567890",
            "email": "ana@example.com",
            "password": "secreto",
        }

    def test_crea_paciente_valido_serializador(self):
        s = PacienteRegistroSerializer(data=self.valid_payload)
        self.assertTrue(s.is_valid(), s.errors)
        obj = s.save()
        self.assertIsNotNone(obj.id)
        self.assertFalse(obj.es_doctor)

    def test_rechaza_es_doctor_en_payload(self):
        payload = dict(self.valid_payload, **{"es_doctor": True})
        s = PacienteRegistroSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("es_doctor", s.errors)

    def test_nss_unico(self):
        Paciente.objects.create(
            nombre="Ana",
            fecha_nacimiento="1990-05-20",
            nss="11111111111",
            email="ana1@example.com",
            password="x",
        )
        payload = dict(self.valid_payload, **{"nss": "11111111111", "email": "otra@example.com"})
        s = PacienteRegistroSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("nss", s.errors)

    def test_email_unico(self):
        Paciente.objects.create(
            nombre="Luis",
            fecha_nacimiento="1988-01-02",
            nss="22222222222",
            email="luis@example.com",
            password="x",
        )
        payload = dict(self.valid_payload, **{"email": "luis@example.com", "nss": "33333333333"})
        s = PacienteRegistroSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

