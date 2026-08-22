# Create your views here.
from django.shortcuts import render


def register_user(request):
    from users.models import Provincia
    context = {'provinces': Provincia.choices}
    return render(request, 'users/register_user.html', context)


from django.views import View
class ResetPasswordPageView(View):
    """Página SSR donde usuario ve form para nueva contraseña"""
    
    def get(self, request, uidb64=None, token=None):
        # Mostrar formulario con los datos ya precargados
        context = {
            'uidb64': uidb64,
            'token': token,
            'valid': True  # Asumimos válido hasta comprobar
        }
        
        # Opcional: validar token aquí mismo
        try:
            from django.utils.encoding import force_str
            from django.contrib import messages
            from django.contrib.auth.tokens import default_token_generator
            from django.contrib.auth import get_user_model
            from django.utils.http import urlsafe_base64_decode
            
            User = get_user_model()
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            if not default_token_generator.check_token(user, token):
                context['valid'] = False
                messages.error(request, 'Enlace inválido o expirado')
                
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            context['valid'] = False
            messages.error(request, 'Enlace inválido o expirado')
        
        return render(request, 'users/reset_pw.html', context)