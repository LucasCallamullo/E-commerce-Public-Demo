


""" 
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from orders.models import Invoice

@receiver(post_save, sender=Invoice)
def send_invoice_email(sender, instance, created, **kwargs):
    # instance hace referencia al objeto modelo agregado en sender
    
    if created:  # Solo se ejecuta cuando la factura es creada por primera vez
        factura_number = f"FAC-{instance.id:06d}"
        subject = 'Pago Confirmado - Gracias por tu compra'
        text_content = f'Hola {instance.name}, tu pago por la factura #{instance.invoice_number} ha sido confirmado.'
        html_content = f'''
            <p>Hola <strong>{instance.name}</strong>,</p>
            <p>Tu pago por la factura <strong>#{factura_number}</strong> ha sido confirmado.</p>
            <p>Gracias por tu compra.</p>
        '''
        msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [instance.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
"""
