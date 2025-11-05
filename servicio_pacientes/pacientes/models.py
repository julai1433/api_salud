from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class PacienteManager(BaseUserManager):
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

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class Paciente(AbstractBaseUser, PermissionsMixin):
    nombre = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    nss = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    es_doctor = models.BooleanField(default=False)
    
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = PacienteManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'nss']

    def __str__(self):
        return f"{self.nombre} ({self.nss})"