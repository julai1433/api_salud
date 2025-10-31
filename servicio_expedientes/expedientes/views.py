from django.db import connection
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from expedientes.models import PacienteIndex, NotaMedica
from expedientes.serializers import NotaMedicaSerializer, NotaMedicaCreateSerializer

def health(request):
    return JsonResponse({"status": "ok"})

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
        serializer = NotaMedicaCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        obj = serializer.save()
        data = NotaMedicaSerializer(obj).data
        return Response(data, status=201)

class ExpedientesBuscarInseguroView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        nss = request.query_params.get("nss", "")
        if not nss:
            return Response({"detail": "nss es requerido"}, status=400)
        sql = f"SELECT id, id_paciente, id_doctor, fecha_consulta, diagnostico, tratamiento FROM expedientes_notamedica WHERE id_paciente IN (SELECT id_paciente FROM expedientes_pacienteindex WHERE nss = '{nss}')"
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
        data = []
        for r in rows:
            data.append({
                "id": r[0],
                "id_paciente": r[1],
                "id_doctor": r[2],
                "fecha_consulta": r[3].isoformat() if r[3] is not None else None,
                "diagnostico": r[4],
                "tratamiento": r[5],
            })
        return Response(data, status=200)