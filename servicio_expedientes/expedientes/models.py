from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class DoctorManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class Doctor(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=100, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = DoctorManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        app_label = 'expedientes_core'

    def __str__(self):
        return self.nombre

class PacienteIndex(models.Model):
    id_paciente = models.IntegerField(unique=True)
    nss = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'expedientes_core'  # Match the new app label
        db_table = 'expedientes_pacienteindex'

    def __str__(self):
        return f"{self.nss} -> {self.id_paciente}"

class NotaMedica(models.Model):
    id_paciente = models.IntegerField()
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    fecha_consulta = models.DateTimeField()
    diagnostico = models.TextField()
    tratamiento = models.TextField()

    def __str__(self):
        return f"Nota para Paciente {self.id_paciente} por {self.doctor.nombre}"