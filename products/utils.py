

def valid_id_or_None(id_value, allow_zero=False):
    """
    Valida que un ID sea un INT positivo y numérico.
    Returns:
        - int: El ID convertido a entero si es válido
        - None: Si el ID es inválido
        
    #### forma acotada para un futuro puede ahorrar milesimas..
    return int(value_id) if value_id and value_id.isdigit() and int(value_id) > 0 else None
    """
    if id_value is None:
        return None
    try:
        id_int = int(id_value)
        if allow_zero:
            return id_int
        
        return id_int if id_int > 0 else None
    except (TypeError, ValueError):
        return None


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


import uuid
def generate_image_name(content_type):
    """Genera un nombre único con extensión basada en el content_type."""
    ext = content_type.split('/')[-1]
    return f"{uuid.uuid4().hex[:13]}.{ext}"


from rest_framework import serializers
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
def parse_number(value, field_name, allow_zero=True):
    """
    Convierte y valida un número recibido como string, float o int.

    - Para campos de tipo precio (Decimal): se espera precisión de 2 decimales.
    - Para campos enteros (stock, descuento): convierte a entero.
    - Si el valor es negativo o inválido, lanza un ValidationError.

    Parámetros:
    - value: el valor recibido del frontend.
    - field_name: nombre del campo para construir el mensaje de error.
    - allow_zero: si se permite que el valor sea igual a 0.

    Returns:
        - Decimal para precios.
        - int para stock o descuento.
    """
    if isinstance(value, str):
        # Formatos como "30.000,50" => "30000.50"
        value = value.replace(".", "").replace(",", ".")

    if field_name.lower() in ('precio', 'precio de lista'):
        try:
            value = Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError):
            raise serializers.ValidationError(f"El {field_name} debe ser un número válido con hasta 2 decimales.")
    elif field_name.lower() in ('stock', 'descuento'):
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError(f"El {field_name} debe ser un número entero válido.")
    else:
        raise serializers.ValidationError(f"Campo '{field_name}' no reconocido para validación.")

    if (allow_zero and value < 0) or (not allow_zero and value <= 0):
        condicion = "mayor o igual a 0" if allow_zero else "mayor que 0"
        raise serializers.ValidationError(f"El {field_name} debe ser {condicion}.")

    return value


import html
def sanitize_text(value: str) -> str:
    if not isinstance(value, str):
        return ""
    return html.escape(value.strip())
    

import unicodedata
import re
def normalize_or_None(text):
    # Check if the text is None or empty
    if not text:
        return None
    
    # Replace plus signs '+' with spaces
    text = text.replace('+', ' ')
    
    # Remove accents
    text_without_accents = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

    # Remove special characters
    text_normalized = re.sub(r'[^\w\s]', '', text_without_accents).strip()

    # Reduce multiple spaces to a single one
    text_normalized = re.sub(r'\s+', ' ', text_normalized)

    return text_normalized


def get_valid_bool(value, field='some field'):
    """
    Validate and convert a given input into a boolean (True or False).

    This function is typically used in serializers or data validation processes
    to ensure that a field expected to be a boolean is correctly interpreted,
    whether it's provided as a string ('true'/'false') or a native boolean type.

    Parameters:
        value: The input value to validate. Can be a string or a boolean.
        field (str): The name of the field being validated (used in error messages).

    Returns:
        bool: The validated boolean value (True or False).

    Raises:
        serializers.ValidationError: If the value is not a valid boolean or
        not a recognizable string representation of a boolean.
    """
    if isinstance(value, str):
        value = value.lower()
        if value in ("true", "1", "yes"):
            return True
        elif value in ("false", "0", "no"):
            return False
        else:
            raise serializers.ValidationError(f"El valor de {field} debe ser 'true' o 'false'.")
    
    elif isinstance(value, bool):
        return value
    
    else:
        raise serializers.ValidationError(f"El campo {field} debe ser booleano.")

