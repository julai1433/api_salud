from rest_framework import serializers
from expedientes.models import NotaMedica, PacienteIndex

class NotaMedicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaMedica
        fields = ["id", "id_paciente", "id_doctor", "fecha_consulta", "diagnostico", "tratamiento"]

class NotaMedicaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaMedica
        fields = ["id_paciente", "id_doctor", "fecha_consulta", "diagnostico", "tratamiento"]

    def validate_id_paciente(self, value):
        if not PacienteIndex.objects.filter(id_paciente=value).exists():
            raise serializers.ValidationError("id_paciente no está indexado")
        return value

