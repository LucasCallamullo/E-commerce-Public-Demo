import uuid
import json
import requests

from django.conf import settings
from requests.exceptions import RequestException


def get_url_from_imgbb(image_file):
    """Sube imagen a ImgBB con manejo robusto de errores"""
    api_key = settings.IMGBB_KEY
    
    # 1. Validar y preparar la imagen (retorna objeto archivo y content_type)
    validated_file, content_type = validate_and_prepare_image(image_file)
    
    # 2. Generar nombre único para el archivo
    unique_name = generate_image_name(content_type)

    try:
        # 2. Subida a ImgBB y manejo de errores
        response = requests.post(
            "https://api.imgbb.com/1/upload",    # endpoint de guardado siempre es el mismo
            params={"key": api_key},    # apikey sacada de imgBB
            files={"image": (unique_name, validated_file)},    # pasameos el nuevo nombre y el archivo
            timeout=10  # Timeout en segundos para reintentar
        )
        response.raise_for_status()  # Lanza error para códigos HTTP 4XX/5XX

        # 3. Procesar respuesta, manejo error o obtengo la url 
        data = response.json()
        
        if not data.get("success"):
            error_msg = data.get("error", {}).get("message", "Error desconocido en ImgBB")
            raise ValueError(f"Error en ImgBB: {error_msg}")

        print('URL:', data["data"]["url"])
        return data["data"]["url"]

    # 4. Respuesta distintos errores
    except RequestException as e:
        raise ValueError("Error de conexión con el servicio de imágenes")
    except json.JSONDecodeError:
        raise ValueError("Respuesta inválida del servicio")
    except Exception as e:
        raise ValueError("Error al procesar la imagen")
    

import os
from PIL import Image
from io import BytesIO
def validate_and_prepare_image(file):
    """Valida la imagen y la prepara para subida. Retorna (file_obj, content_type)."""
    # Validación básica: nombre y tamaño
    if not getattr(file, 'name', None):
        raise ValueError("El archivo no tiene nombre")
    if file.size == 0:
        raise ValueError("El archivo está vacío")

    # Obtener extensión y tipo MIME
    ext = os.path.splitext(file.name)[1][1:].lower() if file.name else 'jpg'
    content_type = getattr(file, 'content_type', f'image/{ext}' if ext else 'image/jpeg')

    # Validar extensión permitida
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Formato '{ext}' no soportado. Use: {', '.join(ALLOWED_EXTENSIONS)}")

    # Validar tamaño máximo (32MB)
    if file.size > 32 * 1024 * 1024:
        raise ValueError("El archivo excede el límite de 32MB")

    # Si el tipo MIME es sospechoso (ej: application/octet-stream), validar con Pillow
    if not content_type.startswith('image/'):
        try:
            # Abrir y verificar integridad de la imagen
            img = Image.open(file)
            img.verify()  # Lanza excepción si la imagen está corrupta
            
            # Convertir a BytesIO para garantizar compatibilidad
            output = BytesIO()
            img = Image.open(file)  # Reabrir porque verify() cierra el archivo
            img.save(output, format='JPEG' if ext in ('jpg', 'jpeg') else ext.upper())
            output.seek(0)
            
            # Actualizar content_type basado en la extensión
            content_type = f'image/{ext if ext in ALLOWED_EXTENSIONS else "jpeg"}'
            return output, content_type

        except Exception as e:
            raise ValueError(f"Archivo no es una imagen válida: {str(e)}")

    # Si el archivo ya es válido, retornarlo tal cual (reiniciando cursor)
    file.seek(0)
    return file, content_type


def generate_image_name(content_type):
    """Genera un nombre único con extensión basada en el content_type."""
    ext = content_type.split('/')[-1]
    return f"{uuid.uuid4().hex[:13]}.{ext}"




