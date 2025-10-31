#!/bin/bash

# Script para demostrar el flujo de uso seguro entre los microservicios de pacientes y expedientes.
# 1. Inicia los servidores de Django.
# 2. Crea un doctor y un paciente.
# 3. El doctor se autentica para obtener un token.
# 4. El doctor crea un expediente para el paciente.
# 5. Se verifica que el expediente fue creado.
# 6. Se detienen los servidores.

# --- Configuración ---
HOST_PACIENTES="http://127.0.0.1:8001"
HOST_EXPEDIENTES="http://127.0.0.1:8002"
UNIQUE_ID=$(date +%s | cut -c 8-)
DOCTOR_EMAIL="doctor-$UNIQUE_ID@clinic.com"
DOCTOR_PASS="password123"
PACIENTE_NSS="NSS-$UNIQUE_ID"
PACIENTE_EMAIL="paciente-$UNIQUE_ID@example.com"
PACIENTE_PASS="password456"

# --- Funciones de Utilidad ---
function print_step {
    echo "-----------------------------------------------------"
    echo "PASO: $1"
    echo "-----------------------------------------------------"
}

function print_info {
    echo "INFO: $1"
}

function check_health {
    print_info "Verificando que el servicio $1 esté activo en $2..."
    if curl -s --head "$2/health/" | head -n 1 | grep "200 OK" > /dev/null; then
        echo "OK: El servicio $1 está respondiendo."
    else
        echo "ERROR: No se pudo conectar con el servicio $1 en $2. Abortando."
        exit 1
    fi
}

# --- Inicio del Script ---

# 1. Iniciar servidores en segundo plano
print_step "Iniciando servicios de Django"
(cd servicio_pacientes && python3 manage.py runserver 8001) &
PID_PACIENTES=$!
(cd servicio_expedientes && python3 manage.py runserver 8002) &
PID_EXPEDIENTES=$!

# Dar tiempo a los servidores para que inicien
sleep 5

# Verificar que ambos servicios estén activos
check_health "Pacientes" $HOST_PACIENTES
check_health "Expedientes" $HOST_EXPEDIENTES

# 2. Crear Doctor y Paciente
print_step "Creando un Doctor y un Paciente"

# Crear Doctor
print_info "Registrando al Doctor: $DOCTOR_EMAIL And NSS: DR-NSS-$UNIQUE_ID"
curl -s -X POST "$HOST_PACIENTES/api/pacientes/seguro/registro" \
-H "Content-Type: application/json" \
-d '{
    "nombre": "Dr. House",
    "fecha_nacimiento": "1970-01-01",
    "nss": "DR-NSS-'$UNIQUE_ID'",
    "email": "'$DOCTOR_EMAIL'",
    "password": "'$DOCTOR_PASS'",
    "es_doctor": true
}' | jq .

# Crear Paciente
print_info "Registrando al Paciente con NSS: $PACIENTE_NSS"
curl -s -X POST "$HOST_PACIENTES/api/pacientes/seguro/registro" \
-H "Content-Type: application/json" \
-d '{
    "nombre": "John Doe",
    "fecha_nacimiento": "1990-05-15",
    "nss": "'$PACIENTE_NSS'",
    "email": "'$PACIENTE_EMAIL'",
    "password": "'$PACIENTE_PASS'"
}' | jq .

# 3. Obtener Token de Autenticación del Doctor
print_step "Obteniendo Token de Autenticación para el Doctor"
AUTH_RESPONSE=$(curl -s -X POST "$HOST_EXPEDIENTES/api-token-auth/" \
-H "Content-Type: application/json" \
-d '{
    "username": "'$DOCTOR_EMAIL'",
    "password": "'$DOCTOR_PASS'"
}')

TOKEN=$(echo $AUTH_RESPONSE | jq -r .token)

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "ERROR: No se pudo obtener el token de autenticación para el doctor. Verifique las credenciales."
    kill $PID_PACIENTES $PID_EXPEDIENTES
    exit 1
fi
print_info "Token obtenido exitosamente."

# 4. Crear Expediente para el Paciente
print_step "Doctor creando un expediente para el Paciente $PACIENTE_NSS"
curl -s -X POST "$HOST_EXPEDIENTES/api/expedientes/seguro/crear" \
-H "Content-Type: application/json" \
-H "Authorization: Token $TOKEN" \
-d '{
    "paciente_nss": "'$PACIENTE_NSS'",
    "id_doctor": 1,
    "fecha_consulta": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "diagnostico": "Fiebre común",
    "tratamiento": "Reposo y acetaminofén"
}' | jq .

# 5. Verificar la creación del expediente
print_step "Verificando que el expediente fue creado para el NSS $PACIENTE_NSS"
curl -s -X GET "$HOST_EXPEDIENTES/api/expedientes/seguro/buscar?nss=$PACIENTE_NSS" \
-H "Authorization: Token $TOKEN" | jq .

# 6. Detener los servidores
print_step "Deteniendo los servidores"
kill $PID_PACIENTES $PID_EXPEDIENTES
print_info "Flujo completado."

exit 0
