from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled

import logging
logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Global exception handler for the REST API.

    This function intercepts all exceptions raised inside DRF views
    (e.g. ValidationError, NotFound, PermissionDenied, etc.) and
    normalizes the error response format across the entire API.

    Flow:
    1. Delegates the exception handling to DRF's default exception_handler.
    2. If DRF is able to convert the exception into a Response:
        - Rewrites the response payload to a unified structure.
    3. If DRF cannot handle the exception:
        - Returns None and lets Django handle it (500 error).

    Standard error response format:
        {
            "success": false,
            "detail": "<human-readable error message>"
        }

    Notes:
    - This handler works transparently with DRF exceptions such as:
        - ValidationError   -> HTTP 400
        - NotFound          -> HTTP 404
        - PermissionDenied  -> HTTP 403
    - Views and helper methods should raise exceptions instead of
      returning Response objects manually.
    - This ensures consistency, cleaner views, and centralized
      error formatting.
    """
    response = exception_handler(exc, context)

    if response is not None:
        detail = response.data
        
        # Caso especial: Errores de validación (400) suelen ser dicts de listas {"campo": ["error"]}
        if isinstance(detail, dict) and "detail" not in detail:
            detail = detail

        # --- Lógica personalizada para Throttling (429) ---
        elif isinstance(exc, Throttled):
            wait_time = int(exc.wait) # Obtenemos los segundos restantes
            
            # Personalizamos el mensaje según el tiempo
            if wait_time < 60:
                mensaje = f"Demasiados intentos. Por favor, reintenta en {wait_time} segundos."
            else:
                minutos = wait_time // 60
                mensaje = f"Demasiados intentos. Por favor, reintenta en {minutos} minuto(s)."
            
            # logg rate limits alcanzados
            user = context['request'].user
            ip = context['request'].META.get('REMOTE_ADDR')
            logger.warning(f"Rate limit alcanzado por: {user} (IP: {ip})")
            detail = mensaje
            
        # Caso general: Extraer el string de 'detail' si existe (aplica para 403, 404)
        elif isinstance(detail, dict):
            detail = detail.get("detail")

        response.data = {
            "success": False,
            "detail": detail,
        }

    return response
