

import mercadopago
from django.conf import settings

sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)


def create_preference_data(order, discount):
    
    # Generar las fechas
    expiration_date_from = generate_datetime(flag='start')
    expiration_date_to = generate_datetime(flag='end', hours_window=order.payment.time)
    
    # get urls for mp payments
    back_urls = get_urls_ngrok(settings.BASE_URL_PAGE)
    
    # Obtener lista de items que nos solicita
    # Al usar check out pro incluiremos al costo de envio si existiera como un item
    items, total_cart = get_items_from_order(order)
    
    # Aplicar descuento en caso de que exista cuando se habilite el modelo de cupones
    if discount > 0:
        items, total_cart = get_items_with_discount(items, discount, total_cart)
    
    # obtener el diccionario con info del comprador
    payer = get_payer_info_from_form(order)
    
    # Diccionario corregido
    preference_data = {
        "items": items,  
        "payer": payer,
        "back_urls": back_urls,
        "auto_return": "approved",    # vuelve al back_url que corresponda en 5 segundos o con el btn
        "payment_methods": {
            "excluded_payment_methods" : [
                { "id" : "argencard" },
                { "id" : "cmr" },
                { "id" : "diners" },
                { "id" : "tarshop" }
            ],
            "excluded_payment_types" : [],
            "installments" : 1
        },
        "notification_url": "https://www.your-site.com/ipn",
        "statement_descriptor": settings.PYME_NAME,
        # fechas calculadas con la fucnion en payments/utils.py
        "expires": True, 
        "expiration_date_from": expiration_date_from,
        "expiration_date_to": expiration_date_to,
        # agregados
        "binary_mode": True, # para tener dos estados pagado o fail
        # "purpose": "wallet_purchase", # para solo permitir que paguen usuarios registrados
        
        # Referencia externa asociada con la orden
        "external_reference": str(order.id),  
    }

    # Crea la preferencia en Mercado Pago
    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]
    
    # Obtiene el ID de la preferencia que se pasa como contexto
    preference_id = preference["id"]
    
    return preference_id, total_cart


def get_items_from_order(order):
    """
    Se espera que la funcion devuelva todos los items almacenados en el carrito del usuario con el formato
    que nos establece mercado pago
    items = [ {
        "id": "item-ID-1234",
        "title": "Producto 1",
        "quantity": 3,
        "unit_price": 100.00,
        "currency_id": "BRL",
        "picture_url": "https://www.mercadopago.com/org-img/MP3/home/logomp3.gif",
        "description": "Descrição do Item",
        "category_id": "art",
    },

    Args:
        user_id (_type_, optional): _description_. Defaults to None.
    """
    items = []
    total_cart = 0

    # Precargar relaciones necesarias si no están ya precargadas    # items_order = order.items.all()
    if not hasattr(order, '_prefetched_objects_cache') or 'items' not in order._prefetched_objects_cache:
        order.items.all().select_related('product')

    # Procesar items
    for item in order.items.all():
        product = item.product
        price = float(item.price)
        quantity = item.quantity
        category_name = (product.category.name or "No Category")[:50]
        
        items.append({
            "id": str(product.id),
            "title": product.name[:255],  # MercadoPago tiene límite de 256 chars
            "quantity": quantity,
            "unit_price": price,
            "currency_id": "ARS",  # Moneda (ajustar según sea necesario)
            "picture_url": product.main_image[:500],  # Límite de URL
            "description": (product.description or '')[:255],
            "category_id": category_name,
        })
        
        # aprovechamos el recorrido para calcular el total cart
        total_cart += price * quantity
        
    # recuperamos el envio method para obtener sus datos y agregarlos a los items
    shipment_method = order.shipment.method
    
    # Al usar check out pro incluiremos al costo de envio si existiera como un item
    items.append({
        "id": shipment_method.id,
        "title": shipment_method.name,
        "quantity": 1, 
        "unit_price": float(shipment_method.price),
        "currency_id": "ARS",  # Moneda (ajustar según sea necesario)
        # "picture_url": item.product.main_image,
        "description": "Precio del envío",
        "category_id": "envío",
    })
    
    total_cart += float(shipment_method.price)    # terminamos de acumular los valores
    
    return items, total_cart
    

def get_items_with_discount(items, discount, total):
    """  
        Esto es para obtener los items con un descuento total aplicado proporcionalmente
        si el descuento fueran 5000, descontaría a todos los items proporcionalmente 5000
    """
    
    # Recalcular precios proporcionalmente
    for item in items:
        item["unit_price"] -= (discount / total) * item["unit_price"]
        
    total_cart = sum(item["unit_price"] * item["quantity"] for item in items)
    
    return items, total_cart


def get_payer_info_from_form(order):
    """
        Funcion para recuperar los datos del payer como nos solicita mercado pago
    
    "payer": {     # ejemplo api mp
        "name": "João",
        "surname": "Silva",
        "email": "user@email.com",
        "phone": {
            "area_code": "11",
            "number": "4444-4444"
        },
        "identification": {
            "type": "CPF",
            "number": "19119119100"
        },
        "address": {
            "street_name": "Street",
            "street_number": 123,
            "zip_code": "06233200"
        }
    },
        
    order (model):
        "name": "Lucas",
        "last_name": "Martinez",
        "email": "lucas.martinez@example.com",
        "cellphone": "3515437688",
        "dni": "41224335",
        "detail_order": "Por favor, entregar antes de las 18:00.",
        
    order.shipment :
        # NOTE if id_envio_method == '1': # this is only for retire local
        "name_retiro": "lucas",
        "dni_retiro": "martinez",
        
        # NOTE if id_envio_method != '1': # Home delivery
        "province": "Córdoba",
        "city": "Córdoba Capital",
        "address": "Av. Colón 1234",
        "postal_code": "5000",
        "detail": "Departamento 2B",
        
        # NOTE this is for use to complete de order
        "envio_method_id": "2", 
        "payment_method_id": "3"
    }
    """
    
    payer = {
        "name": (order.first_name or "")[:25],    # Limit MP
        "surname": (order.last_name or "")[:25],
        "email": (order.email or "")[:50],
        "phone": {
            "area_code": "351",
            "number": (order.cellphone or "")[:15],
        },
        "identification": {
            "type": "DNI",
            "number": (order.dni or "")[:15],
        },
    }
    
    # Solo agregar dirección si no es retiro local (id != 1)
    if order.shipment.method.id != 1:
        # Parsear número de dirección (ej: "Av. Colón 1234" -> "Av. Colón" y "1234")
        address_parts = (order.shipment.address or "").rsplit(' ', 1)
        street_name = address_parts[0] if len(address_parts) > 1 else order.shipment.address
        street_number = address_parts[1] if len(address_parts) > 1 else "0"
        
        payer["address"] = {
            "street_name": (street_name or "")[:100],
            "street_number": street_number[:10],
            "zip_code": (order.shipment.postal_code or "")[:10],
        }
        
    return payer

    
from datetime import datetime, timezone, timedelta
def generate_datetime(flag: str='start', hours_window: int=4, utc_offset: int=-3) -> str:
    """
    Genera una fecha y hora formateada en el estándar ISO 8601.
    
    Args:
        flag (str): Define si se genera la hora de inicio ('start') o fin ('end').
        hours_window (int): Cantidad de horas para la ventana de tiempo.
        utc_offset (int): Desfase horario en horas respecto a UTC. establecido para Argentina
    
    Returns:
        str: Fecha y hora formateada en ISO 8601 con el offset de zona horaria.
    """
    # Obtener la fecha y hora actuales
    now = datetime.now(timezone.utc)  # Hora actual en UTC

    # Ajustar la hora a la zona horaria local
    start_time = now + timedelta(hours=utc_offset)

    # Calcular fecha de inicio o fin
    if flag == 'start':
        target_time = start_time
    elif flag == 'end':
        target_time = start_time + timedelta(hours=hours_window)
    else:
        raise ValueError("El parámetro 'flag' debe ser 'start' o 'end'.")

    # Formatear la fecha y hora
    # Eliminar microsegundos adicionales
    formatted_time = target_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]  
    formatted_time += f"{utc_offset:+03d}:00"  # Agregar el offset de zona horaria
    
    return formatted_time


def get_urls_ngrok(url: str) -> dict:
    """ 
        Obtiene de forma generica las urls necesarias para trabajar con mercado pago
    """
    if url.endswith('/'):
        url = url.rstrip("/")
    
    back_urls = {
        "success": url + "/success/",
        "failure": url + "/failure/",
        "pending": url + "/pending/"
    }
    
    return back_urls