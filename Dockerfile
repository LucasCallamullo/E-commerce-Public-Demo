# Usamos una imagen ligera de Python 3.13
# FROM python:3.13-slim
# Usamos slim-bookworm que es la versión más estable y ligera basada en Debian
FROM python:3.13-slim-bookworm

# Evita que Python genere archivos .pyc y permite ver logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo en el contenedor
WORKDIR /app

# OPTIMIZACIÓN: Instalación y limpieza en un solo paso
# (libpq-dev, gcc) dependencias del sistema necesarias para psycopg2
# (curl) herramientas de red
# (libjpeg-dev, zlib1g-dev) para Pillow (procesar imágenes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    libc-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*


# Instalamos dependencias de Python
# despues reemplazar esta linea en la 32:
# pip install --no-cache-dir -r requirements.txt
COPY requirements.txt .
# a futuro comentar esta linea
COPY requirements-dev.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-dev.txt

# 1. Creamos el usuario primero
RUN useradd -m myuser

# 3. CREAMOS LAS CARPETAS BASE (media y static)
# Al crearlas aquí y hacer chown, myuser es el dueño del "padre".
# Esto permite que Django cree subcarpetas como /app/media/products/ automáticamente.
RUN mkdir -p /app/media /app/static && chown -R myuser:myuser /app

# 4. Copiamos el código
# Usamos --chown para que los archivos del proyecto también sean de myuser
COPY --chown=myuser:myuser . .

# 5. Cambiamos al usuario
USER myuser

# Exponemos el puerto donde correrá Gunicorn (servidor de producción)
EXPOSE 8000

# El comando de inicio lo manejaremos desde el compose