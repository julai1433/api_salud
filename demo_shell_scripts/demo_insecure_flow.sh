#!/bin/bash

# Script para demostrar el flujo de uso de los endpoints INSEGUROS.
# ARQUITECTURA ASUMIDA:
# 1. Se crea un paciente de prueba.
# 2. Se usa el endpoint inseguro de `pacientes` para modificar su perfil sin token.
# 3. Se usa el endpoint inseguro de `expedientes` para buscarlo sin token.

# --- Configuración ---
HOST_PACIENTES="http://127.0.0.1:8001"
HOST_EXPEDIENTES="http://127.0.0.1:8002"
UNIQUE_ID=$(date +%s | cut -c 5-)

# --- Datos del nuevo Paciente ---
PACIENTE_EMAIL="insecure-paciente-$UNIQUE_ID@example.com"
PACIENTE_PASS="password123"
PACIENTE_NSS="INSECURE-NSS-$UNIQUE_ID"

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

# 1. Crear un Paciente de prueba
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

echo "Respuesta de creación de paciente:"
echo $PACIENTE_RESPONSE | jq .

# Extraer el ID y NSS del paciente creado
PACIENTE_ID=$(echo $PACIENTE_RESPONSE | jq -r .id)

if [ "$PACIENTE_ID" == "null" ] || [ -z "$PACIENTE_ID" ]; then
    echo "ERROR: No se pudo crear el paciente de prueba. Abortando."
    kill $PID_PACIENTES $PID_EXPEDIENTES
    exit 1
fi

print_info "Paciente creado con ID: $PACIENTE_ID y NSS: $PACIENTE_NSS"

# 2. Modificar perfil con endpoint inseguro (SIN TOKEN)
print_step "2. Modificando perfil del Paciente $PACIENTE_ID usando endpoint inseguro (sin token)"

NUEVO_NOMBRE="NombreCambiado-$UNIQUE_ID"

UPDATE_RESPONSE=$(curl -s -X PUT "$HOST_PACIENTES/api/pacientes/inseguro/perfil/$PACIENTE_ID" \
-H "Content-Type: application/json" \
-d "{\"nombre\": \"$NUEVO_NOMBRE\"}")

echo "Respuesta de actualización insegura:"
echo $UPDATE_RESPONSE | jq .

# Verificar que el nombre haya cambiado
NOMBRE_ACTUALIZADO=$(echo $UPDATE_RESPONSE | jq -r .nombre)
if [ "$NOMBRE_ACTUALIZADO" == "$NUEVO_NOMBRE" ]; then
    print_info "ÉXITO: El nombre del paciente fue modificado a través del endpoint inseguro."
else
    print_info "FALLO: No se pudo modificar el nombre del paciente."
fi


# 3. Buscar expediente con endpoint inseguro (SIN TOKEN)
print_step "3. Buscando al paciente $PACIENTE_NSS usando endpoint inseguro (sin token)"

# Nota: No hemos creado un expediente, por lo que esperamos una respuesta vacía `[]` con status 200 OK.
# Esto confirma que el endpoint es accesible sin autenticación.
curl -s -X GET "$HOST_EXPEDIENTES/api/expedientes/inseguro/buscar?nss=$PACIENTE_NSS" | jq .

print_info "La prueba finaliza si la petición anterior devolvió una lista (aunque esté vacía) sin errores de autenticación."


# Finalizar
print_step "Deteniendo los servidores"
kill $PID_PACIENTES $PID_EXPEDIENTES
print_info "Flujo completado."

exit 0
