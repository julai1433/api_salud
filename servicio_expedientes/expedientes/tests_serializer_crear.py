from django.test import TestCase
from django.utils import timezone
from expedientes.models import NotaMedica
from expedientes.models import PacienteIndex
from expedientes.serializers import NotaMedicaCreateSerializer

class NotaMedicaCreateSerializerTests(TestCase):
    def setUp(self):
        self.idx = PacienteIndex.objects.create(id_paciente=10, nss="01234567890")
        self.valid_payload = {
            "id_paciente": 10,
            "id_doctor": 99,
            "fecha_consulta": timezone.now().isoformat(),
            "diagnostico": "Gripe fuerte",
            "tratamiento": "Reposo",
        }

    def test_serializador_valido_crea_nota(self):
        s = NotaMedicaCreateSerializer(data=self.valid_payload)
        self.assertTrue(s.is_valid(), s.errors)
        obj = s.save()
        self.assertIsNotNone(obj.id)
        self.assertEqual(obj.id_paciente, 10)

    def test_falta_campo_obligatorio(self):
        p = dict(self.valid_payload)
        del p["diagnostico"]
        s = NotaMedicaCreateSerializer(data=p)
        self.assertFalse(s.is_valid())
        self.assertIn("diagnostico", s.errors)

    def test_id_paciente_no_indexado_error(self):
        p = dict(self.valid_payload)
        p["id_paciente"] = 9999
        s = NotaMedicaCreateSerializer(data=p)
        self.assertFalse(s.is_valid())
        self.assertIn("id_paciente", s.errors)

