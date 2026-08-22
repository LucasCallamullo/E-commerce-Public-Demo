#!/bin/bash

# --- PASO 1: CARGAR CONFIGURACIÓN ---
# Leemos el .env para saber nombres de contenedores si fuera necesario
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | tr -d '\r' | xargs)
elif [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | tr -d '\r' | xargs)
fi

# --- PASO 2: UBICACIÓN DEL SCRIPT ---
# Esto asegura que el script funcione aunque lo lances desde afuera de la carpeta
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# --- PASO 3: CONFIGURAR DESTINO ---
# Ajustamos el nombre del contenedor al nuevo: web_client_1
CONTAINER_NAME="web_client_1" 
BACKUP_DIR="./scripts/backups/media"
TIMESTAMP=$(date +%Y-%m-%d_%H%M)
FILENAME="media_backup_$TIMESTAMP.tar.gz"

# Creamos la carpeta en tu PC/WSL si no existe
mkdir -p "$BACKUP_DIR"

echo "-------------------------------------------"
echo "Iniciando Backup de Archivos Media (Imágenes)..."
echo "Contenedor origen: $CONTAINER_NAME"
echo "Destino local: $BACKUP_DIR/$FILENAME"
echo "-------------------------------------------"


# --- PASO 4: EXTRACCIÓN ---
# 1. 'docker exec $CONTAINER_NAME' -> Entra al contenedor ($CONTAINER_NAME que definimos arriba)
# 2. 'tar -cz -C /app media' -> Comprime la carpeta /app/media ADENTRO del contenedor
# 3. '> "$BACKUP_DIR/$FILENAME"' -> Saca ese paquete y lo guarda en tu carpeta de Windows/WSL
docker exec $CONTAINER_NAME tar -cz -C /app media > "$BACKUP_DIR/$FILENAME"


# --- PASO 5: VALIDACIÓN ---
# Verificamos si el archivo se creó y no está vacío (tamaño mayor a 0 bytes)
if [ -s "$BACKUP_DIR/$FILENAME" ]; then
    echo "ÉXITO: El backup de media se guardó correctamente."
    # Listamos el contenido del backup para estar seguros (opcional)
    echo "Primeros archivos encontrados en el backup:"
    tar -ztf "$BACKUP_DIR/$FILENAME" | head -n 5
    echo "..."
else
    echo "ERROR: El backup falló. Asegurate de que '$CONTAINER_NAME' esté corriendo."
    rm -f "$BACKUP_DIR/$FILENAME"
    exit 1
fi


# --- PASO 6: LIMPIEZA (ROTACIÓN) ---
# Borra backups de media viejos (más de 30 días)
find "$BACKUP_DIR" -type f -name "*.tar.gz" -mtime +30 -delete

echo "-------------------------------------------"
echo "Proceso finalizado."