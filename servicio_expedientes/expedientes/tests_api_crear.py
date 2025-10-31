from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.utils import timezone
from expedientes.models import PacienteIndex, NotaMedica

class ExpedientesCrearAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/expedientes/seguro/crear"
        self.user = User.objects.create_user(username="tester", password="pass1234")
        self.token = Token.objects.create(user=self.user)
        self.auth = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}
        PacienteIndex.objects.create(id_paciente=10, nss="01234567890")

        self.valid_payload = {
            "id_paciente": 10,
            "id_doctor": 99,
            "fecha_consulta": timezone.now().isoformat(),
            "diagnostico": "Gripe fuerte",
            "tratamiento": "Reposo",
        }

    def test_requiere_token(self):
        resp = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(resp.status_code, 401)

    def test_crea_nota_201(self):
        resp = self.client.post(self.url, self.valid_payload, format="json", **self.auth)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("id", data)
        self.assertEqual(data["id_paciente"], 10)
        self.assertEqual(data["diagnostico"], "Gripe fuerte")

    def test_id_paciente_no_indexado_400(self):
        payload = dict(self.valid_payload, **{"id_paciente": 9999})
        resp = self.client.post(self.url, payload, format="json", **self.auth)
        self.assertEqual(resp.status_code, 400)

    def test_fecha_consulta_invalida_400(self):
        payload = dict(self.valid_payload, **{"fecha_consulta": "no-es-una-fecha"})
        resp = self.client.post(self.url, payload, format="json", **self.auth)
        self.assertEqual(resp.status_code, 400)

