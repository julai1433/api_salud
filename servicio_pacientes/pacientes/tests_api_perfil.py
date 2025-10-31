from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from pacientes.models import Paciente

class PacientesPerfilAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url_base = "/api/pacientes/seguro/perfil/"
        self.user = User.objects.create_user(username="tester", password="pass1234")
        self.token = Token.objects.create(user=self.user)
        self.auth = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}

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

    def test_put_parcial_actualiza_200_sin_password(self):
        url = f"{self.url_base}{self.paciente.id}"
        payload = {"nombre": "Ana López"}
        resp = self.client.put(url, payload, format="json", **self.auth)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["nombre"], "Ana López")
        self.assertNotIn("password", data)

    def test_put_id_inexistente_404(self):
        url = f"{self.url_base}999999"
        resp = self.client.put(url, {"nombre": "X"}, format="json", **self.auth)
        self.assertEqual(resp.status_code, 404)

    def test_put_email_duplicado_409(self):
        url = f"{self.url_base}{self.paciente.id}"
        payload = {"email": "luis@example.com"}
        resp = self.client.put(url, payload, format="json", **self.auth)
        self.assertEqual(resp.status_code, 409)

    def test_put_rechaza_es_doctor_400(self):
        url = f"{self.url_base}{self.paciente.id}"
        payload = {"es_doctor": True}
        resp = self.client.put(url, payload, format="json", **self.auth)
        self.assertEqual(resp.status_code, 400)

    def test_put_parcial_actualiza_fecha_nacimiento(self):
        url = f"{self.url_base}{self.paciente.id}"
        payload = {"fecha_nacimiento": "1991-06-21"}
        resp = self.client.put(url, payload, format="json", **self.auth)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["fecha_nacimiento"], "1991-06-21")

