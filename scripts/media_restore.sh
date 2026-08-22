#!/bin/bash
# 1. Cargar variables desde el archivo .env
# Limpiamos los \r de Windows si existieran para que no rompa en Linux/Docker
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | tr -d '\r' | xargs)
elif [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | tr -d '\r' | xargs)
else
    echo "Error: No se encontró el archivo .env"
    exit 1
fi

# --- PASO 2: UBICACIÓN DEL SCRIPT ---
# Esto asegura que el script funcione aunque lo lances desde afuera de la carpeta
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

CONTAINER_NAME="web_client_1"

# 2. Elegir el backup más reciente
LATEST_MEDIA=$(ls -t ./scripts/backups/media/*.tar.gz 2>/dev/null | head -1)

if [ -z "$LATEST_MEDIA" ]; then
    echo "ERROR: No se encontró ningún backup en ./backups/media"
    exit 1
fi

echo "Restaurando desde: $LATEST_MEDIA"

# 3. Restauración (Con fix para Git Bash)
# Usamos MSYS_NO_PATHCONV para que /app no se convierta a C:/Program Files...
MSYS_NO_PATHCONV=1 docker exec -i $CONTAINER_NAME tar -xz -C /app < "$LATEST_MEDIA"

# 4. Ajustar permisos (Con fix para Git Bash)
echo "Ajustando permisos para myuser..."
MSYS_NO_PATHCONV=1 docker exec -u root $CONTAINER_NAME chown -R myuser:myuser /app/media

if [ $? -eq 0 ]; then
    echo "ÉXITO: Restauración completa."
else
    echo "HUBO UN ERROR."
fi