# Documento de Análisis de Vulnerabilidades

## Introducción
El proyecto **Microservicios Salud** implementa dos servicios independientes en Django REST Framework: `servicio_pacientes` gestiona el ciclo de vida de pacientes y `servicio_expedientes` mantiene notas médicas asociadas. Ambos servicios se comunican mediante API REST y scripts/colecciones de Postman que muestran tanto flujos legítimos como ataques deliberados para fines académicos. Este documento analiza las vulnerabilidades intencionales que se dejaron en endpoints “inseguros” para demostrar los riesgos de omitir abstracciones y validaciones.

## Análisis del Endpoint de Búsqueda

### Código inseguro
```python
# servicio_expedientes/expedientes/views.py:56
class ExpedientesBuscarInseguroView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        nss = request.query_params.get("nss", "")
        if not nss:
            return Response({"detail": "nss es requerido"}, status=400)
        nota_table = NotaMedica._meta.db_table
        index_table = PacienteIndex._meta.db_table
        sql = (
            "SELECT id, id_paciente, doctor_id, fecha_consulta, diagnostico, tratamiento "
            f"FROM {nota_table} "
            f"WHERE id_paciente IN (SELECT id_paciente FROM {index_table} WHERE nss = '{nss}')"
        )
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
        ...
```

### Vulnerabilidad (SQL Injection)
El parámetro `nss` se concatena directamente en la cadena SQL. Un atacante puede cerrar la comilla e inyectar condiciones siempre verdaderas (`' OR '1'='1`). El motor de base de datos ejecutará el SQL modificado y devolverá expedientes sin autorización.

### Petición que explota la vulnerabilidad
En la colección Postman `Microservicios Salud`, el request **“Inyección SQL (inseguro)”** del folder *Flujo Ataque* invoca:
```
GET {{expedientes_base}}/api/expedientes/inseguro/buscar?nss=' OR '1'='1
```
El test asociado verifica que la respuesta es un arreglo con registros obtenidos ilegítimamente.

### Código seguro y mitigación
```python
# servicio_expedientes/expedientes/views.py:25
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
```
El endpoint seguro usa el ORM (`objects.get`, `objects.filter`) que parametriza las consultas y evita que el NSS manipule directamente el SQL generado. Además restringe el acceso a usuarios autenticados.

## Análisis del Endpoint de Registro/Perfil

### Código inseguro
```python
# servicio_pacientes/pacientes/views.py:55
class PacientesInseguroPerfilView(APIView):
    permission_classes = [AllowAny]

    def put(self, request, pk):
        Paciente.objects.filter(pk=pk).update(**request.data)
        paciente = get_object_or_404(Paciente, pk=pk)
        ...
```

### Vulnerabilidad (Asignación Masiva)
El payload se pasa sin filtrado a `update(**request.data)`. Si el atacante incluye campos sensibles (por ejemplo `es_doctor`), éstos se aplican sin validación ni autorización, escalando privilegios.

### Petición que explota la vulnerabilidad
En Postman, el request **“Asignación masiva (inseguro)”** del folder *Flujo Ataque* envía:
```json
PUT {{pacientes_base}}/api/pacientes/inseguro/perfil/{{paciente_b_id}}
{
  "es_doctor": true
}
```
El test confirma que el campo `es_doctor` se cambia a `true`, otorgando indebidamente permisos de doctor.

### Código seguro y mitigación
```python
# servicio_pacientes/pacientes/views.py:33
class PacientesPerfilSeguroView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        paciente = get_object_or_404(Paciente, pk=pk)
        serializer = PacientePerfilUpdateSerializer(instance=paciente, data=request.data, partial=True)
        ...
        obj = serializer.save()
        ...
```
```python
# servicio_pacientes/pacientes/serializers.py:39
class PacientePerfilUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = ["nombre", "fecha_nacimiento", "email"]
```
El endpoint seguro obliga a autenticación y delega la actualización al serializer, que define explícitamente los campos aceptados (`fields`). Cualquier intento de modificar `es_doctor` o `nss` se descarta, previniendo Asignación Masiva.

## Conclusiones
El contraste entre los endpoints “inseguros” y sus contrapartes protegidas demuestra la importancia de usar capas de abstracción (ORM) y validación (serializers) que provee el framework. Construir SQL manual o mapear payloads directamente a modelos expone la aplicación a ataques críticos como SQL Injection o escalamiento de privilegios. Apegarnos a herramientas declarativas y controles de autenticación reduce errores humanos y fortalece la seguridad de los microservicios.
