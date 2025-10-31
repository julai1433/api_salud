from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.utils import timezone
from expedientes.models import NotaMedica
from expedientes.models import PacienteIndex  # índice local nss→id_paciente

class ExpedientesBuscarSeguroAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/expedientes/seguro/buscar"
        self.user = User.objects.create_user(username="tester", password="pass1234")
        self.token = Token.objects.create(user=self.user)
        self.auth = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}

        # Índice local: nss→id_paciente
        self.idx_ana = PacienteIndex.objects.create(id_paciente=1, nss="01234567890")
        self.idx_luis = PacienteIndex.objects.create(id_paciente=2, nss="11111111111")

        # Notas médicas (solo algunas de Ana; otras de Luis para asegurar filtrado)
        NotaMedica.objects.create(
            id_paciente=1, id_doctor=10,
            fecha_consulta=timezone.now(),
            diagnostico="Gripe",
            tratamiento="Reposo",
        )
        NotaMedica.objects.create(
            id_paciente=1, id_doctor=11,
            fecha_consulta=timezone.now(),
            diagnostico="Alergia",
            tratamiento="Antihistamínico",
        )
        NotaMedica.objects.create(
            id_paciente=2, id_doctor=10,
            fecha_consulta=timezone.now(),
            diagnostico="Migraña",
            tratamiento="Analgésico",
        )

    def test_requiere_token(self):
        resp = self.client.get(self.url, {"nss": "01234567890"}, format="json")
        self.assertEqual(resp.status_code, 401)

    def test_busca_por_nss_devuelve_solo_notas_del_paciente(self):
        resp = self.client.get(self.url, {"nss": "01234567890"}, format="json", **self.auth)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertTrue(all(item["id_paciente"] == 1 for item in data))
        # Campos mínimos esperados
        for item in data:
            self.assertIn("id", item)
            self.assertIn("id_paciente", item)
            self.assertIn("id_doctor", item)
            self.assertIn("fecha_consulta", item)
            self.assertIn("diagnostico", item)
            self.assertIn("tratamiento", item)

    def test_nss_inexistente_devuelve_lista_vacia(self):
        resp = self.client.get(self.url, {"nss": "99999999999"}, format="json", **self.auth)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_parametro_nss_requerido(self):
        resp = self.client.get(self.url, format="json", **self.auth)
        self.assertEqual(resp.status_code, 400)

