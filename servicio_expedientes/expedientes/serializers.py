from rest_framework import serializers
from .models import Doctor, NotaMedica, PacienteIndex
from rest_framework.exceptions import ValidationError

class DoctorRegistroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['nombre', 'email', 'password', 'especialidad']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return Doctor.objects.create_user(**validated_data)

class NotaMedicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaMedica
        fields = ["id", "id_paciente", "doctor", "fecha_consulta", "diagnostico", "tratamiento"]
        depth = 1 # Para mostrar los detalles del doctor

class NotaMedicaCreateSerializer(serializers.ModelSerializer):
    paciente_nss = serializers.CharField(write_only=True)

    class Meta:
        model = NotaMedica
        fields = ["paciente_nss", "fecha_consulta", "diagnostico", "tratamiento"]

    def create(self, validated_data):
        nss = validated_data.pop('paciente_nss')
        doctor = validated_data.pop('doctor')  # El doctor se inyecta desde la vista

        try:
            index_entry = PacienteIndex.objects.get(nss=nss)
        except PacienteIndex.DoesNotExist:
            # Return a 400 with a clear message instead of raising IntegrityError (500)
            raise ValidationError({'paciente_nss': 'Índice de paciente no existe. Cree primero el paciente en el servicio de pacientes.'})

        # Create the nota médica using the found index_entry
        nota_medica = NotaMedica.objects.create(
            doctor=doctor,
            id_paciente=index_entry.id_paciente,
            **validated_data
        )
        return nota_medica
