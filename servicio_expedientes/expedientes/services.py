from django.conf import settings
from .models import PacienteIndex
import requests

def sync_paciente_index(nss, id_paciente):
    """
    Sincroniza un paciente con el índice local
    """
    try:
        index, created = PacienteIndex.objects.get_or_create(
            nss=nss,
            defaults={'id_paciente': id_paciente}
        )
        return True
    except Exception as e:
        print(f"Error sincronizando paciente: {e}")
        return False

def get_paciente_by_nss(nss):
    """
    Obtiene datos del paciente desde el servicio de pacientes usando NSS
    """
    try:
        response = requests.get(
            f"{settings.PACIENTES_API_URL}/pacientes/by-nss/{nss}",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as e:
        print(f"Error comunicándose con servicio_pacientes: {e}")
        return None