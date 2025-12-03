


from django.template.loader import render_to_string

from favorites.utils import get_favs_products
from products.filters import VALUES_CARDS_LIST
from products.utils import valid_id_or_None

from home.models import Store
from orders.models import Order, ItemOrder
from orders.models import ShipmentMethod, PaymentMethod, StatusOrder
from users.models import CustomUser


from products.serializers import ProductListSerializer


def profile_tabs_user(user, tab_name):
    if tab_name == 'orders-tab':
        orders = (
            Order.objects.filter(user=user)
            .values('id', 'created_at', 'total', 'status__name')
            .order_by('-updated_at')
        )
        return { 
            'orders': list(orders),
            'is_admin': False
        }
    
    if tab_name == 'favorites-tab':
        favorites_ids = get_favs_products(user)
        products = (
            get_favs_products(user, return_qs=True, favorites_ids=favorites_ids)
            .values(*VALUES_CARDS_LIST).order_by('price', 'id')
        )
        serializer = ProductListSerializer(products, many=True, context={'favorites_ids': favorites_ids})
        return {'products': serializer.data}

    if tab_name == 'invoices-tab':
        # proximamente...
        return {"invoices": None}



def profile_tabs_admin(request, tab_name):
    """
        Handles data retrieval for different admin profile tabs based on the tab name.

        Args:
            request (HttpRequest): The HTTP request object containing GET parameters.
            tab_name (str): The identifier for the tab to load data for. Possible values:
                - 'orders-tab'
                - 'store-data-tab'
                - 'users-tab'

        Returns:
            dict: A dictionary containing data relevant to the requested tab, ready to be used 
            in a JSON response or template context.

        Tab behaviors:

        1. 'orders-tab':
            - Optionally filters orders by order ID or status ID from GET parameters.
            - Returns:
                - 'orders': list of orders (each order is a dict with id, created_at, total, status name).
                - 'status_orders': list of possible order statuses (id and name).
                - 'status_id': currently selected status ID (or None).
                - 'is_admin': always True, indicating admin privileges.

        2. 'store-data-tab':
            - Retrieves the store info (single object), shipping methods, and payment methods.
            - Returns:
                - 'store': dict with store data.
                - 'shipments': list of shipping methods.
                - 'payments': list of payment methods.

        3. 'users-tab':
            - Supports filtering users by search term (email) and role (defaulting to 'buyer').
            - Returns:
                - 'users': list of user dictionaries with selected fields.
                - 'choices': dictionary mapping role keys to role names (for select inputs).
                - 'choice': the currently selected role filter (for UI state).

        Note:
        - Uses Django ORM `.values()` to return dictionaries instead of full model instances.
        - Uses helper function `valid_id_or_None` to safely parse IDs from query parameters.
    """
    if tab_name == 'orders-tab':
        order_id = valid_id_or_None(request.GET.get('order_id', None))
        status_id = valid_id_or_None(request.GET.get('status', None))
        
        orders = Order.objects.all()
        if order_id:
            orders = orders.filter(id=order_id)
        if status_id and not order_id:
            orders = orders.filter(status_id=status_id)
            
        # get a dict values for orders
        orders = orders.values('id', 'created_at', 'total', 'status__name').order_by('-updated_at')

        # get a dict values for status_orders
        status_orders = StatusOrder.objects.values('id', 'name').order_by('id')
        
        return { 
            'orders': list(orders),    # convert a list to responseJson
            'status_orders': list(status_orders),
            'status_id': status_id,
            'is_admin': True 
        }
    
    if tab_name == 'store-data-tab':
        shipments = ShipmentMethod.objects.values(
            'id', 'name', 'price', 'is_active', 'description'
        ).order_by('id')
        
        payments = PaymentMethod.objects.values(
            'id', 'name', 'time', 'is_active', 'description'
        ).order_by('id')
        
        store = Store.objects.values(
            'id', 'name', 'address', 'email', 'cellphone', 'name', 'ig_url', 'fb_url', 'tt_url',
            'wsp_number', 'google_url', 'tw_url'
        ).get(id=1)
        
        return {
            'store': store,    # al ser unico devuelve el dict
            'shipments': list(shipments),    # convert a list to responseJson
            'payments': list(payments)
        }
    
    if tab_name == 'users-tab':
        # Recuperar parámetros GET
        search = request.GET.get('search', '')   # Si no hay, devuelve ''
        role = request.GET.get('role', 'buyer')  # Por defecto 'buyer'

        users = CustomUser.objects.all()
        if search:
            users = users.filter(email__icontains=search)
        if role:
            users = users.filter(role=role)
            
        # Solo obtener los campos necesarios
        users = users.values('id', 'first_name', 'last_name', 'email', 'role')

        return {
            'users': list(users),
            'choices': dict(CustomUser.ROLE_CHOICES),
            'choice': role,   # Para que tu <select> quede marcado
        }