from django.shortcuts import render

# Create your views here.
from orders.models import ShipmentMethod, PaymentMethod
from orders.utils import get_order_detail_context

def order_detail(request, order_id):
    user = request.user
    if not user.is_authenticated:    # Stupids checks for problematic users
        return render(request, "payments/fail_payments.html", {"error": "Debes iniciar sesión para pagar."})
    
    context = get_order_detail_context(order_id, user)
    if not context:
        render(request, "payments/fail_payments.html", {"error": "Order Not Found."})
    
    return render(request, "orders/order_detail.html", context)


from django.db.models import FloatField
from django.db.models.functions import Cast

def resume_order(request):
    from users.choices import PROVINCIAS_CHOICES
    """ 
        Esta vista se llama para ver el formulario (se valida con serializers), ver opciones
        de metodos de pago y envío, y actuar en consecuencia segun el metodo de pago y envío.
    """
    if not request.user.is_authenticated:
        context = {'flag_to_login': True}
        return render(request, "users/register_user.html", context)
        
    # Obtenemos los distintos envios y metodos de pago para actualizar dinamicamente

    # esto convierte directamente el valor Decimal en Float
    # list es opcional para cachear en memoria el queryset
    # cada queryset es lazy por lo tanto se ejecuta cada vez que lo recorro si no lo cacheo
    shipment_methods = list(
        ShipmentMethod.objects.filter(is_active=True)  # 1. Filtra solo métodos activos
        .annotate(  # 2. Agrega campos calculados a cada fila
            price_float=Cast('price', output_field=FloatField())  # Convierte 'price' a Float
        )
        .values('id', 'name', 'price_float')  # 3. Selecciona solo los campos que quieres
    )
    
    payment_methods = (
        PaymentMethod.objects.filter(is_active=True)
        .values('id', 'name', 'description')
    )
    
    context = {
        'shipment_methods': shipment_methods,
        'payment_methods': payment_methods,
        'provinces': PROVINCIAS_CHOICES
    }
    
    return render(request, "orders/resume_order.html", context)
