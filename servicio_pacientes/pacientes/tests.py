from django.test import TestCase
from django.db import IntegrityError
from pacientes.models import Paciente

class PacienteModelTests(TestCase):
    def test_crea_paciente_valido(self):
        p = Paciente.objects.create(
            nombre="Ana López",
            fecha_nacimiento="1990-05-20",
            nss="01234567890",
            email="ana@example.com",
            password="secreto",
        )
        self.assertIsNotNone(p.id)
        self.assertFalse(p.es_doctor)

    def test_nss_unico(self):
        Paciente.objects.create(
            nombre="Ana",
            fecha_nacimiento="1990-05-20",
            nss="11111111111",
            email="ana1@example.com",
            password="x",
        )
        with self.assertRaises(IntegrityError):
            Paciente.objects.create(
                nombre="Ana2",
                fecha_nacimiento="1991-06-21",
                nss="11111111111",
                email="ana2@example.com",
                password="y",
            )

    def test_email_unico(self):
        Paciente.objects.create(
            nombre="Luis",
            fecha_nacimiento="1988-01-02",
            nss="22222222222",
            email="luis@example.com",
            password="x",
        )
        with self.assertRaises(IntegrityError):
            Paciente.objects.create(
                nombre="Luis2",
                fecha_nacimiento="1989-02-03",
                nss="33333333333",
                email="luis@example.com",
                password="y",
            )

