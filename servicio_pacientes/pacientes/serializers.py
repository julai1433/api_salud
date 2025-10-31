from rest_framework import serializers
from pacientes.models import Paciente

class PacienteRegistroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = ["nombre", "fecha_nacimiento", "nss", "email", "password", "es_doctor"]

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
        fields = ["nombre", "fecha_nacimiento", "email", "password"]  # nss es inmutable en este endpoint

    def validate(self, attrs):
        allowed = set(self.Meta.fields)
        unexpected = set(self.initial_data.keys()) - allowed
        if "es_doctor" in unexpected:
            raise serializers.ValidationError({"es_doctor": "Campo no permitido"})
        if "nss" in self.initial_data:
            raise serializers.ValidationError({"nss": "NSS es inmutable"})
        return attrs

    def validate_email(self, value):
        qs = Paciente.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Email ya registrado")
        return value
