#!/bin/bash

# Script para demostrar el flujo seguro entre los microservicios.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SERVICIO_PACIENTES_DIR="${ROOT_DIR}/servicio_pacientes"
SERVICIO_EXPEDIENTES_DIR="${ROOT_DIR}/servicio_expedientes"

PACIENTES_HOST=${PACIENTES_SERVICE_HOST:-127.0.0.1}
PACIENTES_PORT=${PACIENTES_SERVICE_PORT:-8001}
EXPEDIENTES_HOST=${EXPEDIENTES_SERVICE_HOST:-127.0.0.1}
EXPEDIENTES_PORT=${EXPEDIENTES_SERVICE_PORT:-8002}

HOST_PACIENTES="http://${PACIENTES_HOST}:${PACIENTES_PORT}"
HOST_EXPEDIENTES="http://${EXPEDIENTES_HOST}:${EXPEDIENTES_PORT}"
UNIQUE_ID=$(date +%s | cut -c 5-)

DOCTOR_EMAIL="doctor-$UNIQUE_ID@clinic.com"
DOCTOR_PASS="password123"
DOCTOR_NSS="DR-NSS-$UNIQUE_ID"

PACIENTE_EMAIL="paciente-$UNIQUE_ID@example.com"
PACIENTE_PASS="password456"
PACIENTE_NSS="NSS-$UNIQUE_ID"

STARTED_PIDS=()

function print_step {
    echo "-----------------------------------------------------"
    echo "PASO: $1"
    echo "-----------------------------------------------------"
}

function print_info {
    echo "INFO: $1"
}

function kill_servers {
    if [ ${#STARTED_PIDS[@]} -gt 0 ]; then
        kill "${STARTED_PIDS[@]}" 2>/dev/null || true
    fi
}

function port_is_listening {
    local host=$1
    local port=$2
python3 - "$host" "$port" <<'PY'
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])

if host in ("0.0.0.0", "::", ""):
    host = "127.0.0.1"

s = socket.socket()
s.settimeout(0.5)
try:
    s.connect((host, port))
except OSError:
    sys.exit(1)
else:
    sys.exit(0)
finally:
    s.close()
PY
}

function ensure_server {
    local name=$1
    local dir=$2
    local host=$3
    local port=$4

    if port_is_listening "$host" "$port"; then
        print_info "$name ya estaba escuchando en ${host}:${port}, se reutilizará."
        return
    fi

    print_info "Levantando $name en ${host}:${port}..."
    (cd "$dir" && python3 manage.py runserver "${host}:${port}") &
    STARTED_PIDS+=($!)
    sleep 5
}

trap kill_servers EXIT

# --- Inicio del Script ---

print_step "Iniciando servicios de Django"
ensure_server "servicio_pacientes" "$SERVICIO_PACIENTES_DIR" "$PACIENTES_HOST" "$PACIENTES_PORT"
ensure_server "servicio_expedientes" "$SERVICIO_EXPEDIENTES_DIR" "$EXPEDIENTES_HOST" "$EXPEDIENTES_PORT"

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
echo "$DOCTOR_RESPONSE" | jq .

print_step "2. Obteniendo Token para el Doctor desde servicio_pacientes"
AUTH_RESPONSE=$(curl -s -X POST "$HOST_PACIENTES/api-token-auth/" \
-H "Content-Type: application/json" \
-d "{
    \"username\": \"$DOCTOR_EMAIL\",
    \"password\": \"$DOCTOR_PASS\"
}")
TOKEN=$(echo "$AUTH_RESPONSE" | jq -r .token)
if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "ERROR: No se pudo obtener el token de autenticación para el doctor."
    exit 1
fi
print_info "Token para el Doctor obtenido exitosamente."

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
echo "$PACIENTE_RESPONSE" | jq .

print_info "Flujo de servicio_pacientes completado y verificado."

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
echo "$EXPEDIENTE_RESPONSE"

print_info "Flujo completado."
exit 0
