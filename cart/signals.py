
"""
from cart.carrito import Carrito

# user_logged_in
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.core.cache import cache

import logging
logger = logging.getLogger(__name__)

@receiver(user_logged_out)
def clear_cart_on_logout(sender, request, user, **kwargs):
    
    if not user:
        return
    
    if hasattr(request, 'session'):
        cart_session = Carrito(request)
        cart_data = cart_session.carrito
        
        if cart_data:
            logger.debug("Cart cleared for: %s", user.first_name)
            
            # IMPORTANTE: Guardamos el dato en el objeto request 
            # solo para pasarlo al middleware en esta MISMA petición.
            request._cart_to_restore = cart_data
            
            logger.debug("[CART DICT] --> %s", cart_data)



from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.core.cache import cache

import logging
logger = logging.getLogger(__name__)

@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    # Siempre hay user aquí (siempre autenticado)
    print(f"User logged in: {user.username}")
    
    
        
    # Ejemplos de cosas útiles que podrías hacer:
    # - sincronizar carrito guardado en DB con el de sesión
    # - restaurar carrito previo
    # - registrar log de actividad
    
""" 