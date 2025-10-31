from django.test import TestCase
from expedientes.models import NotaMedica
from django.utils import timezone

class NotaMedicaModelTests(TestCase):
    def test_crea_nota_valida(self):
        n = NotaMedica.objects.create(
            id_paciente=1,
            id_doctor=99,
            fecha_consulta=timezone.now(),
            diagnostico="Gripe estacional",
            tratamiento="Reposo e hidratación",
        )
        self.assertIsNotNone(n.id)

    def test_fecha_consulta_requerida(self):
        with self.assertRaises(Exception):
            NotaMedica.objects.create(
                id_paciente=1,
                id_doctor=2,
                diagnostico="X",
                tratamiento="Y",
            )

