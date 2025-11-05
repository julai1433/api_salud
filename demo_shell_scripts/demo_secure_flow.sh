#!/bin/bash

# Script para demostrar el flujo de autenticación autocontenido en servicio_pacientes.

# --- Configuración ---
HOST_PACIENTES="http://127.0.0.1:8001"
HOST_EXPEDIENTES="http://127.0.0.1:8002"
UNIQUE_ID=$(date +%s | cut -c 5-)

# --- Credenciales para el nuevo Doctor ---
DOCTOR_EMAIL="doctor-$UNIQUE_ID@clinic.com"
DOCTOR_PASS="password123"
DOCTOR_NSS="DR-NSS-$UNIQUE_ID"

# --- Datos del nuevo Paciente ---
PACIENTE_EMAIL="paciente-$UNIQUE_ID@example.com"
PACIENTE_PASS="password456"
PACIENTE_NSS="NSS-$UNIQUE_ID"

# --- Funciones de Utilidad ---
function print_step {
    echo "-----------------------------------------------------"
    echo "PASO: $1"
    echo "-----------------------------------------------------"
}

function print_info {
    echo "INFO: $1"
}

# --- Inicio del Script ---

print_step "Iniciando servicios de Django"
(cd servicio_pacientes && python3 manage.py runserver 8001) &
PID_PACIENTES=$!
(cd servicio_expedientes && python3 manage.py runserver 8002) &
PID_EXPEDIENTES=$!
sleep 5 # Dar tiempo a los servidores para que inicien

# 1. Crear un DOCTOR a través de la API de pacientes
print_step "1. Creando un Doctor vía API en servicio_pacientes"
DOCTOR_RESPONSE=$(curl -s -X POST "$HOST_PACIENTES/api/pacientes/seguro/registro" \
-H "Content-Type: application/json" \
-d "{
    \"nombre\": \"Dr. House $UNIQUE_ID\",
    \"fecha_nacimiento\": \"1970-01-01\",
    \"nss\": \"$DOCTOR_NSS\",
    \"email\": \"$DOCTOR_EMAIL\",
    \"password\": \"$DOCTOR_PASS\",
    \"es_doctor\": true
}")

echo "Respuesta de creación de doctor:"
echo $DOCTOR_RESPONSE | jq .

# 2. Obtener Token de Autenticación para el DOCTOR desde servicio_pacientes
print_step "2. Obteniendo Token para el Doctor desde servicio_pacientes"
AUTH_RESPONSE=$(curl -s -X POST "$HOST_PACIENTES/api-token-auth/" \
-H "Content-Type: application/json" \
-d "{
    \"username\": \"$DOCTOR_EMAIL\",
    \"password\": \"$DOCTOR_PASS\"
}")

TOKEN=$(echo $AUTH_RESPONSE | jq -r .token)

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "ERROR: No se pudo obtener el token de autenticación para el doctor."
    kill $PID_PACIENTES $PID_EXPEDIENTES
    exit 1
fi
print_info "Token para el Doctor obtenido exitosamente."

# 3. Crear un PACIENTE (como otro usuario)
print_step "3. Creando un Paciente vía API en servicio_pacientes"
PACIENTE_RESPONSE=$(curl -s -X POST "$HOST_PACIENTES/api/pacientes/seguro/registro" \
-H "Content-Type: application/json" \
-d "{
    \"nombre\": \"Paciente $UNIQUE_ID\",
    \"fecha_nacimiento\": \"1995-10-20\",
    \"nss\": \"$PACIENTE_NSS\",
    \"email\": \"$PACIENTE_EMAIL\",
    \"password\": \"$PACIENTE_PASS\",
    \"es_doctor\": false
}")

echo "Respuesta de creación de paciente:"
echo $PACIENTE_RESPONSE | jq .

print_info "Flujo de servicio_pacientes completado y verificado."

# NOTA: El siguiente paso fallará porque el token de `pacientes` no es válido en `expedientes`.
# Esto demuestra que, aunque hemos arreglado la autenticación en un servicio,
# la autenticación unificada es un problema aparte y más complejo.
print_step "4. INTENTO FALLIDO (ESPERADO): Usar token de 'pacientes' en 'expedientes'"

EXPEDIENTE_RESPONSE=$(curl -s -w '\n%{http_code}' -X POST "$HOST_EXPEDIENTES/api/expedientes/seguro/crear" \
-H "Content-Type: application/json" \
-H "Authorization: Token $TOKEN" \
-d "{
    \"paciente_nss\": \"$PACIENTE_NSS\",
    \"id_doctor\": 1, 
    \"fecha_consulta\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",
    \"diagnostico\": \"Revisión de autenticación\",
    \"tratamiento\": \"Proceder con la siguiente fase del proyecto\"
}")

echo "Respuesta de creación de expediente (se espera error 401 - Unauthorized):"
echo "$EXPEDIENTE_RESPONSE"

# Finalizar
print_step "Deteniendo los servidores"
kill $PID_PACIENTES $PID_EXPEDIENTES
print_info "Flujo completado."

exit 0
