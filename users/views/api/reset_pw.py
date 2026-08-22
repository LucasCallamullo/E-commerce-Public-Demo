# api/views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.utils import timezone

from django.contrib.auth import get_user_model
User = get_user_model()

# para crear mensaje dinamico
from home.services.store import StoreService
import re
import hashlib

class PasswordResetRequestView(APIView):
    """Solicitar reset de password (envía email)"""
    permission_classes = [AllowAny]
    # para rate limit 3/min
    throttle_scope = 'email_reset' 

    def post(self, request):
        
        
        email = request.data.get('email', '').strip().lower()
        
        # 1. Validaciones básicas de formato
        if not email or not self._validate_email_format(email):
            return Response({'detail': 'Email inválido'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. CAPA DE SEGURIDAD: Verificar límite por EMAIL en Caché (antes de ir a la DB)
        cache_key = self._get_email_cache_key(email)
        if not self._check_rate_limit(cache_key):
            return Response({
                'detail': 'Demasiadas solicitudes para este correo. Espera 5 minutos.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 3. Registro preventivo del intento (para evitar enumeración de usuarios)
        # Registramos el intento tanto si existe como si no para que el tiempo de respuesta sea igual.
        self._register_attempt(cache_key)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Respuesta genérica por seguridad
            return Response({'detail': 'Si el email existe, recibirás un enlace.'}, status=status.HTTP_200_OK)

        # 4. Proceso de envío de email - Generar token | Construir enlace ssr de views html
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = f"{settings.BASE_URL_PAGE}/reset-password/{uid}/{token}/"
        
        # Enviar email
        store = StoreService.get_public_store(store_id=1)
        subject = f"Restablecer contraseña - {store['name']}"

        message = f"""
            Hola {user.first_name},
            Para restablecer tu contraseña, haz clic en el siguiente enlace:
            {reset_url}
            Este enlace expira en 24 horas.
            Si no solicitaste esto, ignora este email.
        """
        
        html_message = render_to_string('emails/pw_reset_api.html', {
            'user': user,
            'reset_url': reset_url,
            'expiry_hours': 24,
            'store': store
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return Response({'detail': 'Email de recuperación enviado'}, status=status.HTTP_200_OK)

    # --- MÉTODOS DE APOYO PARA CACHÉ ---
    
    def _get_email_cache_key(self, email):
        """Genera una clave única y segura basada en el email"""
        email_hash = hashlib.sha256(email.encode()).hexdigest()
        return f"pwd_rst_{email_hash}"

    def _check_rate_limit(self, cache_key):
        """Verifica si el email puede solicitar otro reset"""
        data = cache.get(cache_key)
        if not data:
            return True
        
        # Máximo 3 intentos por ventana de 24h
        if data['count'] >= 3:
            time_since_first = timezone.now() - data['first_request']
            if time_since_first.total_seconds() < 86400:
                return False
        
        # Mínimo 5 minutos entre envíos
        time_since_last = timezone.now() - data['last_request']
        if time_since_last.total_seconds() < 300:
            return False
            
        return True

    def _register_attempt(self, cache_key):
        """Registra el intento en el caché"""
        data = cache.get(cache_key)
        now = timezone.now()
        
        if not data:
            data = {
                'count': 1,
                'first_request': now,
                'last_request': now
            }
        else:
            data['count'] += 1
            data['last_request'] = now
        
        cache.set(cache_key, data, 60*60*25) # 25 horas

    def _validate_email_format(self, email):
        """Valida formato básico de email"""
        # 1 Dominios comunes inválidos (opcional)
        # invalid_domains = ('example.com', 'test.com', 'mailinator.com')
        # domain = email.split('@')[-1]
        # if domain in invalid_domains:
        #    return False
        
        # 1. Patrón regex básico
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False
        
        # 2. Usar validador de Django (más robusto)
        try:
            validate_email(email)
            return True
        except ValidationError:
            return False


class PasswordResetConfirmView(APIView):
    """Confirmar reset con token y establecer nueva password"""
    permission_classes = [AllowAny]
    throttle_scope = 'email_reset'
    
    def post(self, request):
        uidb64 = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        if not all([uidb64, token, new_password]):
            return Response(
                {'detail': 'Todos los campos son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 1. Primero obtenemos al usuario
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'detail': 'Enlace inválido o expirado'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Validamos el token ANTES de validar la complejidad del password (ahorra CPU)
        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Enlace inválido o expirado'}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Ahora que sabemos que el usuario y el token son reales, validamos la nueva clave
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            # e.messages devuelve una lista, tu handler la envolverá en "detail"
            return Response({'detail': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Todo OK, guardamos
        user.set_password(new_password)
        user.save()
        
        return Response({'detail': 'Contraseña restablecida exitosamente'}, status=status.HTTP_200_OK)
        