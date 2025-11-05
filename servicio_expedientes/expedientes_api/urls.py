"""
URL configuration for expedientes_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path
from expedientes.views import (
    health,
    ExpedientesBuscarSeguroView,
    ExpedientesCrearSeguroView,
    ExpedientesBuscarInseguroView,
    DoctorRegistroView,
    PacienteIndexSyncView,
)
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health),
    path('api-token-auth/', obtain_auth_token),
    # Nueva ruta para registrar doctores
    path('api/expedientes/doctor/registro', DoctorRegistroView.as_view()),
    path('api/expedientes/paciente-index/sync', PacienteIndexSyncView.as_view()),
    path('api/expedientes/seguro/buscar', ExpedientesBuscarSeguroView.as_view()),
    path('api/expedientes/seguro/crear', ExpedientesCrearSeguroView.as_view()),
    path('api/expedientes/inseguro/buscar', ExpedientesBuscarInseguroView.as_view()),
]
