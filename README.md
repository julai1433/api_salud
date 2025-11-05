# API Salud – Microservicios Pacientes y Expedientes

Repositorio con dos microservicios Django REST Framework que modelan un flujo médico sencillo:

- `servicio_pacientes`: registro, autenticación y mantenimiento de perfiles de pacientes.
- `servicio_expedientes`: gestión de doctores y notas médicas sincronizadas con el servicio de pacientes.

El proyecto incluye scripts Bash y una colección Postman para demostrar flujos seguros y ataques controlados (SQL Injection y Asignación Masiva) con fines académicos.

## Estructura relevante

- `servicio_pacientes/` y `servicio_expedientes/`: proyectos Django independientes.
- `start_services.sh`: arranca ambos servicios, reutilizando procesos en ejecución.
- `demo_*_flow.sh`: scripts Bash que automatizan distintos escenarios (seguro, inseguro, ataque).
- `Postman/`: colección y entorno listos para importar.
- `../docs/analisis_vulnerabilidades.md`: informe con el análisis técnico de las vulnerabilidades demostradas.

## Requisitos previos

- Python 3.10+ con virtualenv (recomendado).
- `pip install -r servicio_pacientes/requirements.txt` y `pip install -r servicio_expedientes/requirements.txt` dentro de sus respectivos entornos (o un entorno compartido).
- Opcional: Postman para ejecutar la colección.

## Puesta en marcha rápida

1. Activa tu entorno virtual.
2. Desde `api_salud/` ejecuta:
   ```bash
   ./start_services.sh
   ```
   El script usará `PACIENTES_SERVICE_HOST/PORT` y `EXPEDIENTES_SERVICE_HOST/PORT` si están definidos; de lo contrario asumirá `127.0.0.1:8001/8002`.
3. Si necesitas detener los servicios iniciados por el script, presiona `Ctrl+C`.

## Demos CLI

Con los servicios en marcha puedes lanzar cualquiera de los scripts:

- `./demo_secure_flow.sh` – flujo completo sin vulnerabilidades.
- `./demo_insecure_flow.sh` – reproduce los endpoints vulnerables.
- `./demo_attack_flow.sh` – demuestra la explotación de SQL Injection y asignación masiva.

Cada script documenta su avance en consola (y en `log_demo_attack.txt` para el de ataques).

## Colección Postman

1. Importa `Postman/SaludMicroservicios.postman_collection.json`.
2. Importa el entorno `Postman/MicroserviciosSaludLocal.postman_environment.json`.
3. Selecciona el entorno y usa el Runner para ejecutar la colección completa. Los pre-request scripts generan correos, NSS y tokens automáticamente, replicando los mismos escenarios de los demos Bash.

## Documentación de vulnerabilidades

El archivo `../docs/analisis_vulnerabilidades.md` reúne:

- Código inseguro de ambos microservicios y explicación de las vulnerabilidades.
- Peticiones Postman que las explotan.
- Contraparte segura y motivos por los que evitan el ataque.
- Conclusiones sobre las capas de abstracción y validación.

## Licencia

Proyecto con fines educativos. Ajusta y reutiliza el contenido según tus necesidades.
