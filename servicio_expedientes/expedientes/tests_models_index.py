from django.test import TestCase
from expedientes.models import PacienteIndex

class PacienteIndexModelTests(TestCase):
    def test_crea_indice_local(self):
        idx = PacienteIndex.objects.create(id_paciente=123, nss="22222222222")
        self.assertIsNotNone(idx.id)
        self.assertEqual(idx.id_paciente, 123)
        self.assertEqual(idx.nss, "22222222222")

