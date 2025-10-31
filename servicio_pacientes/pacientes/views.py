from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from pacientes.serializers import PacienteRegistroSerializer, PacientePerfilUpdateSerializer
from pacientes.models import Paciente

def health(request):
    return JsonResponse({"status": "ok"})

class PacientesRegistroSeguroView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PacienteRegistroSerializer(data=request.data)
        if not serializer.is_valid():
            errors = serializer.errors
            if "nss" in errors or "email" in errors:
                return Response(errors, status=409)
            return Response(errors, status=400)
        obj = serializer.save()
        data = {
            "id": obj.id,
            "nombre": obj.nombre,
            "fecha_nacimiento": str(obj.fecha_nacimiento),
            "nss": obj.nss,
            "email": obj.email,
            "es_doctor": obj.es_doctor,
        }
        return Response(data, status=201)

class PacientesPerfilSeguroView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        paciente = get_object_or_404(Paciente, pk=pk)
        serializer = PacientePerfilUpdateSerializer(instance=paciente, data=request.data, partial=True)
        if not serializer.is_valid():
            errors = serializer.errors
            if "email" in errors:
                return Response(errors, status=409)
            return Response(errors, status=400)
        obj = serializer.save()
        data = {
            "id": obj.id,
            "nombre": obj.nombre,
            "fecha_nacimiento": str(obj.fecha_nacimiento),
            "nss": obj.nss,
            "email": obj.email,
            "es_doctor": obj.es_doctor,
        }
        return Response(data, status=200)
    
class PacientesInseguroPerfilView(APIView):
    permission_classes = [AllowAny]

    def put(self, request, pk):
        Paciente.objects.filter(pk=pk).update(**request.data)
        paciente = get_object_or_404(Paciente, pk=pk)
        data = {
            "id": paciente.id,
            "nombre": paciente.nombre,
            "fecha_nacimiento": str(paciente.fecha_nacimiento),
            "nss": paciente.nss,
            "email": paciente.email,
            "es_doctor": paciente.es_doctor,
        }
        return Response(data, status=200)
