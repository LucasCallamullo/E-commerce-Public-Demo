

from core.utils.utils_parsers import valid_id_or_None

from products.services.product import ProductService
from products.services.brand import BrandService
from products.services.category import CategoryService

from home.services.store import StoreService

from orders.services.invoices import InvoiceService
from orders.services.orders import OrderService
from orders.services.status_orders import StatusOrderService
from orders.services.payment_methods import PaymentMethodService
from orders.services.shipment_methods import ShipmentMethodService

from users.services.users import UserService

def profile_tabs_user(user, tab_name):
    
    if tab_name == 'orders-tab':
        orders = OrderService.get_user_orders(user=user)
        return {'orders': orders, 'is_admin': False }
    
    if tab_name == 'favorites-tab':
        # aunque obtiene productos filtrados por favoritos, realmente es para hacer uso futuro de
        # cards + modals por eso los metodos de los otros servicios llaman al resto de componentes
        # necesarios para cards + modals
        products = ProductService.for_favorites_list(user=user)

        # get unique brands on page for some utils on products_cards
        brand_ids = {p['brand_id'] for p in products}

        return {
            'products': products,
            'brands': BrandService.get_brands_list(brand_ids=brand_ids),
            'categories': CategoryService.get_categories_list()
        }

    if tab_name == 'invoices-tab':
        invoices = InvoiceService.get_user_invoices(user=user)
        return {'invoices': invoices, 'is_admin': False }


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
        
        return { 
            # get a list of dict values for orders and status orders
            'orders': OrderService.get_admin_orders(order_id=order_id, status_id=status_id),   
            'status_orders': StatusOrderService.for_filters(),
            'status_id': status_id,
            'is_admin': True
        }
    
    if tab_name == 'users-tab':
        # Recuperar parámetros GET
        search = request.GET.get('search', '')
        role = request.GET.get('role', 'buyer')

        return {
            'users': UserService.get_admin_users(search=search, role=role),
            # 'users': [],
            'choices': UserService.get_role_choices(),
            'choice': role,
        }
        
    if tab_name == 'store-data-tab':
        return {
            'message': "falta hacer todavía"
        }