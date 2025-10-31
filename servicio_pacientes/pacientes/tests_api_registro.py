from django.test import TestCase
from rest_framework.test import APIClient
from pacientes.models import Paciente

class PacientesRegistroAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/pacientes/seguro/registro"
        self.valid_payload = {
            "nombre": "Ana López",
            "fecha_nacimiento": "1990-05-20",
            "nss": "01234567890",
            "email": "ana@example.com",
            "password": "secreto",
        }

    def test_post_registro_valido_201_sin_password(self):
        resp = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("id", data)
        self.assertEqual(data["nombre"], "Ana López")
        self.assertNotIn("password", data)
        self.assertFalse(data.get("es_doctor", False))

    def test_post_con_es_doctor_rechazado_400(self):
        payload = dict(self.valid_payload, **{"es_doctor": True})
        resp = self.client.post(self.url, payload, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_post_nss_duplicado_409(self):
        Paciente.objects.create(
            nombre="Preexistente",
            fecha_nacimiento="1980-01-01",
            nss="99999999999",
            email="pre@ex.com",
            password="x",
        )
        payload = dict(self.valid_payload, **{"nss": "99999999999", "email": "nuevo@ex.com"})
        resp = self.client.post(self.url, payload, format="json")
        self.assertEqual(resp.status_code, 409)

    def test_post_email_duplicado_409(self):
        Paciente.objects.create(
            nombre="Preexistente",
            fecha_nacimiento="1980-01-01",
            nss="88888888888",
            email="dup@example.com",
            password="x",
        )
        payload = dict(self.valid_payload, **{"email": "dup@example.com", "nss": "77777777777"})
        resp = self.client.post(self.url, payload, format="json")
        self.assertEqual(resp.status_code, 409)

