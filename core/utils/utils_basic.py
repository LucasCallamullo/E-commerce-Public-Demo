

def valid_id_or_None(
    id_value: int | str | None, 
    allow_zero: bool = False
    ) -> int | None:
    """
    Valida que un ID sea un INT positivo y numérico.
    Si allow_zero esta activado, permite devolver cero.
    
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
        
        if allow_zero and id_int == 0:
            return id_int
    
        return id_int if id_int > 0 else None
    
    except (TypeError, ValueError):
        return None


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


# maybe deprecated
def sanitize_text(value: str) -> str:
    import html
    
    if not isinstance(value, str):
        return ""
    return html.escape(value.strip())
    

def normalize_or_None(text):
    import unicodedata
    import re
    
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

    return text_normalized.lower()


def get_valid_bool(value, field='some field'):
    """
    Validate and convert a given input into a boolean (True or False).

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
