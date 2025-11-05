#!/bin/bash
set -euo pipefail

PACIENTES_HOST=${PACIENTES_SERVICE_HOST:-127.0.0.1}
PACIENTES_PORT=${PACIENTES_SERVICE_PORT:-8001}
EXPEDIENTES_HOST=${EXPEDIENTES_SERVICE_HOST:-127.0.0.1}
EXPEDIENTES_PORT=${EXPEDIENTES_SERVICE_PORT:-8002}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STARTED_PIDS=()

cleanup() {
    if [ ${#STARTED_PIDS[@]} -gt 0 ]; then
        echo "Deteniendo servicios iniciados por este script..."
        kill "${STARTED_PIDS[@]}" 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM

port_is_listening() {
    local host="$1"
    local port="$2"
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

ensure_server() {
    local name="$1"
    local rel_dir="$2"
    local host="$3"
    local port="$4"

    if port_is_listening "$host" "$port"; then
        echo "INFO: ${name} ya se encuentra ejecutándose en ${host}:${port}, se reutilizará."
        return
    fi

    echo "INFO: Iniciando ${name} en ${host}:${port}..."
    (cd "${ROOT_DIR}/${rel_dir}" && python3 manage.py runserver "${host}:${port}") &
    STARTED_PIDS+=($!)
    sleep 2
}

echo "Iniciando microservicios..."
ensure_server "servicio_pacientes" "servicio_pacientes" "$PACIENTES_HOST" "$PACIENTES_PORT"
ensure_server "servicio_expedientes" "servicio_expedientes" "$EXPEDIENTES_HOST" "$EXPEDIENTES_PORT"

if [ ${#STARTED_PIDS[@]} -eq 0 ]; then
    echo "Ambos servicios ya estaban activos. Este script permanecerá a la espera (Ctrl+C para salir)."
else
    echo "Servicios iniciados. Presiona Ctrl+C para detenerlos."
fi

wait "${STARTED_PIDS[@]:-}"
