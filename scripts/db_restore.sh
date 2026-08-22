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

# 2. Elegir el archivo más reciente
LATEST_BACKUP=$(ls -t ./scripts/backups/db/*.sql.gz 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "Error: No se encontraron archivos de backup en ./scripts/backups/db/"
    exit 1
fi

echo "Restaurando desde: $LATEST_BACKUP"

# 3. Restaurar con PGPASSWORD inyectada
# Usamos -e para pasar la variable de entorno directamente al comando psql
zcat "$LATEST_BACKUP" | docker exec -i -e PGPASSWORD="$DB_PASSWORD" db_client_1 psql -U "$DB_USER" -d "$DB_NAME"

# Verificar si el comando anterior fue exitoso
if [ $? -eq 0 ]; then
    echo "¡Restauración completada con éxito!"
else
    echo "Hubo un error durante la restauración."
fi