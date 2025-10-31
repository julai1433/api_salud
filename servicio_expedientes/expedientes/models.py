from django.db import models

class NotaMedica(models.Model):
    id_paciente = models.IntegerField()
    id_doctor = models.IntegerField()
    fecha_consulta = models.DateTimeField()
    diagnostico = models.TextField()
    tratamiento = models.TextField()

    def __str__(self):
        return f"Nota {self.id} - Paciente {self.id_paciente}"

class PacienteIndex(models.Model):
    id_paciente = models.IntegerField()
    nss = models.CharField(max_length=11, unique=True)

    def __str__(self):
        return f"{self.nss} -> {self.id_paciente}"
