#!/bin/bash

# Script para demostrar el flujo de uso de los endpoints INSEGUROS.

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

PACIENTE_EMAIL="insecure-paciente-$UNIQUE_ID@example.com"
PACIENTE_PASS="password123"
PACIENTE_NSS="INSECURE-NSS-$UNIQUE_ID"

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

print_step "Iniciando servicios de Django"
ensure_server "servicio_pacientes" "$SERVICIO_PACIENTES_DIR" "$PACIENTES_HOST" "$PACIENTES_PORT"
ensure_server "servicio_expedientes" "$SERVICIO_EXPEDIENTES_DIR" "$EXPEDIENTES_HOST" "$EXPEDIENTES_PORT"

print_step "1. Creando un Paciente de prueba para usar en los endpoints inseguros"
PACIENTE_RESPONSE=$(curl -s -X POST "$HOST_PACIENTES/api/pacientes/seguro/registro" \
-H "Content-Type: application/json" \
-d "{
    \"nombre\": \"Victima-$UNIQUE_ID\",
    \"fecha_nacimiento\": \"2000-01-01\",
    \"nss\": \"$PACIENTE_NSS\",
    \"email\": \"$PACIENTE_EMAIL\",
    \"password\": \"$PACIENTE_PASS\"
}")
echo "$PACIENTE_RESPONSE" | jq .

PACIENTE_ID=$(echo "$PACIENTE_RESPONSE" | jq -r .id)
if [ "$PACIENTE_ID" == "null" ] || [ -z "$PACIENTE_ID" ]; then
    echo "ERROR: No se pudo crear el paciente de prueba. Abortando."
    exit 1
fi
print_info "Paciente creado con ID: $PACIENTE_ID y NSS: $PACIENTE_NSS"

print_step "2. Modificando perfil del Paciente $PACIENTE_ID usando endpoint inseguro (sin token)"
NUEVO_NOMBRE="NombreCambiado-$UNIQUE_ID"
UPDATE_RESPONSE=$(curl -s -X PUT "$HOST_PACIENTES/api/pacientes/inseguro/perfil/$PACIENTE_ID" \
-H "Content-Type: application/json" \
-d "{\"nombre\": \"$NUEVO_NOMBRE\"}")
echo "$UPDATE_RESPONSE" | jq .

NOMBRE_ACTUALIZADO=$(echo "$UPDATE_RESPONSE" | jq -r .nombre)
if [ "$NOMBRE_ACTUALIZADO" == "$NUEVO_NOMBRE" ]; then
    print_info "ÉXITO: El nombre del paciente fue modificado a través del endpoint inseguro."
else
    print_info "FALLO: No se pudo modificar el nombre del paciente."
fi

print_step "3. Buscando al paciente $PACIENTE_NSS usando endpoint inseguro (sin token)"
curl -s -X GET "$HOST_EXPEDIENTES/api/expedientes/inseguro/buscar?nss=$PACIENTE_NSS" | jq .
print_info "La prueba finaliza si la petición anterior devolvió una lista (aunque esté vacía) sin errores de autenticación."

print_info "Flujo completado."
exit 0
