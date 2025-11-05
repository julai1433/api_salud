from django.db import connection
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from .models import PacienteIndex, NotaMedica, Doctor
from .serializers import NotaMedicaSerializer, NotaMedicaCreateSerializer, DoctorRegistroSerializer
from .services import sync_paciente_index
import requests

def health(request):
    return JsonResponse({"status": "ok"})

class DoctorRegistroView(APIView):
    permission_classes = [AllowAny] # Cualquiera puede registrar un doctor

    def post(self, request):
        serializer = DoctorRegistroSerializer(data=request.data)
        if serializer.is_valid():
            doctor = serializer.save()
            return Response({"id": doctor.id, "email": doctor.email, "nombre": doctor.nombre}, status=201)
        return Response(serializer.errors, status=400)

class ExpedientesBuscarSeguroView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        nss = request.query_params.get("nss")
        if not nss:
            return Response({"detail": "nss es requerido"}, status=400)
        try:
            idx = PacienteIndex.objects.get(nss=nss)
        except PacienteIndex.DoesNotExist:
            return Response([], status=200)
        notas = NotaMedica.objects.filter(id_paciente=idx.id_paciente).order_by("id")
        data = NotaMedicaSerializer(notas, many=True).data
        return Response(data, status=200)

class ExpedientesCrearSeguroView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Inyecta el doctor autenticado en los datos del serializador
        serializer = NotaMedicaCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Pasa el doctor autenticado al método create del serializador
            obj = serializer.save(doctor=request.user)
            data = NotaMedicaSerializer(obj).data
            return Response(data, status=201)
        return Response(serializer.errors, status=400)

class ExpedientesBuscarInseguroView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        nss = request.query_params.get("nss", "")
        if not nss:
            return Response({"detail": "nss es requerido"}, status=400)
        nota_table = NotaMedica._meta.db_table
        index_table = PacienteIndex._meta.db_table
        # NOTA: La columna ahora es 'doctor_id' por el ForeignKey
        sql = (
            "SELECT id, id_paciente, doctor_id, fecha_consulta, diagnostico, tratamiento "
            f"FROM {nota_table} "
            f"WHERE id_paciente IN (SELECT id_paciente FROM {index_table} WHERE nss = '{nss}')"
        )
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
        data = []
        for r in rows:
            data.append({
                "id": r[0],
                "id_paciente": r[1],
                "doctor_id": r[2],
                "fecha_consulta": r[3].isoformat() if r[3] is not None else None,
                "diagnostico": r[4],
                "tratamiento": r[5],
            })
        return Response(data, status=200)

class NotaMedicaCreateView(APIView):
    def post(self, request):
        nss = request.data.get('paciente_nss')
        
        # Intentar encontrar el índice
        try:
            index = PacienteIndex.objects.get(nss=nss)
        except PacienteIndex.DoesNotExist:
            # Si no existe, intentar sincronizar
            try:
                response = requests.get(f"{settings.PACIENTES_API_URL}/pacientes/by-nss/{nss}")
                if response.status_code == 200:
                    paciente_data = response.json()
                    sync_paciente_index(nss, paciente_data['id'])
                    index = PacienteIndex.objects.get(nss=nss)
                else:
                    return Response(
                        {"error": "Paciente no encontrado"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            except Exception as e:
                return Response(
                    {"error": f"Error sincronizando paciente: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Continuar con la creación del expediente
        # ...existing code...


class PacienteIndexSyncView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        nss = request.data.get("nss")
        id_paciente = request.data.get("id_paciente")

        if not nss or id_paciente is None:
            return Response(
                {"detail": "nss e id_paciente son requeridos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if sync_paciente_index(nss, id_paciente):
            return Response({"status": "ok"}, status=status.HTTP_200_OK)

        return Response(
            {"detail": "No se pudo sincronizar el índice de paciente"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
