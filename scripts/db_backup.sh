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

echo "Cargando configuración para el usuario: $DB_USER"

# 2. Configuración de rutas y nombres
BACKUP_DIR="./scripts/backups/db"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
DB_CONTAINER=$DB_HOST  # Ahora es 'db_client_1'
DB_NAME=$DB_NAME       # Ahora es 'ecommerce_prod'
DB_USER=$DB_USER       # Ahora es 'admin_client1'

# Crear carpeta de backups si no existe
mkdir -p $BACKUP_DIR

echo "Iniciando backup de la base de datos: $DB_NAME..."

# 3. Crear el backup
# IMPORTANTE: Cambiamos $postgres_PASSWORD por $DB_PASSWORD
docker exec -e PGPASSWORD="$DB_PASSWORD" $DB_CONTAINER pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/db_backup_$TIMESTAMP.sql

# 4. Comprimir para ahorrar espacio (pasa de pesar megas a pocos KB)
gzip $BACKUP_DIR/db_backup_$TIMESTAMP.sql

# 5. Rotación: Borrar archivos con más de 7 días para no llenar el disco de la VPS
find $BACKUP_DIR -type f -name "*.sql.gz" -mtime +7 -delete

echo "Backup de DB completado: $TIMESTAMP"
echo "Archivo guardado en: $BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"