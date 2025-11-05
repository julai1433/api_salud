from rest_framework import serializers
from django.conf import settings
import requests

from pacientes.models import Paciente

class PacienteRegistroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = ["nombre", "fecha_nacimiento", "nss", "email", "password", "es_doctor"]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Usa el manager del modelo para crear el usuario y hashear la contraseña
        user = Paciente.objects.create_user(**validated_data)

        payload = {"nss": user.nss, "id_paciente": user.id}
        try:
            url = f"{settings.EXPEDIENTES_API_URL}/expedientes/paciente-index/sync"
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code >= 400:
                print(f"Error sincronizando índice de paciente en expedientes: {response.status_code} - {response.text}")
        except requests.RequestException as exc:
            print(f"Error comunicándose con servicio_expedientes: {exc}")

        return user

    def validate_nss(self, value):
        if Paciente.objects.filter(nss=value).exists():
            raise serializers.ValidationError("NSS ya registrado")
        return value

    def validate_email(self, value):
        if Paciente.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email ya registrado")
        return value


class PacientePerfilUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = ["nombre", "fecha_nacimiento", "email"]

    def validate_email(self, value):
        qs = Paciente.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Email ya registrado")
        return value
