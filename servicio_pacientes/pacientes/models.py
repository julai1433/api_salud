from django.db import models

class Paciente(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    nss = models.CharField(max_length=11, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    es_doctor = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre} ({self.nss})"

