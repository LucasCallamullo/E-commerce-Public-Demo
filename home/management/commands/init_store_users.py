
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

# --- Configuration Objects ---
# These dictionaries centralize the initial data, making it easy to 
# modify values without altering the underlying logic.

# Initial Store configuration
STORE_DATA = {
    "name": "Cat Cat Games",
    "defaults": {
        "wsp_number": "3515437688",
        "address": "Calle Falsa 123",
        "cellphone": "351 543-7688",
        "email": "cat_cat_games@gmail.com",
    }
}

# Initial User configuration
USER_CONFIG = {
    "owner_email": "admin@gmail.com",
    "proofs": True  # Set to False to skip sample data in production
}

# --- Module Availability Check ---
# Prevents script execution if the required 'home' application is missing.
STOP_SCRIPT = False
try:
    from home.models import Store, StoreImage, SocialMedia
except ImportError:
    logger.warning("[HOME APP] The 'home' app is not installed or models are missing.")
    STOP_SCRIPT = True


class Command(BaseCommand):
    """
    Django Management Command to seed the database with initial required data.
    
    Usage: python manage.py <your_command_name>
    This command initializes the Store instance, default images, social media profiles,
    and the administrative/testing user accounts.
    """
    help = "Exclusively executes initial data seeding for the application."

    def handle(self, *args, **kwargs):
        """
        Main execution logic for the command.
        
        Coordinates the initialization process by calling specialized service classes 
        (StoreInit and UserInit) using the predefined configuration dictionaries.
        """
        
        # Guard clause to ensure all dependencies are met
        if STOP_SCRIPT:
            self.stdout.write(self.style.ERROR("Script execution stopped: Missing dependencies."))
            return
        
        # 1. Initialize Store Data
        # Returns the Store instance to ensure it exists before creating related data.
        StoreInit.load_store_init(STORE_DATA)

        # 2. Initialize User Accounts
        # Unpacks USER_CONFIG dictionary into keyword arguments for the service method.
        UserInit.load_users_init(**USER_CONFIG)

        # Final Success Feedback
        # logger.debug("[COMMAND] Database initialization completed successfully.")
        self.stdout.write(self.style.SUCCESS("Setup finished successfully."))


class UserInit:
    """
    Service class responsible for initializing the user database with default accounts.
    Handles the creation of administrators, developers, and test users (sellers/buyers).
    """

    # Default configuration values for development/initial setup
    EMAIL_DEV = "lucas.callamullo.dev@gmail.com"
    PW_DEFAULT = "1234"
    EMAIL_DEF_CLIENT = "anon@gmail.com"
    
    @staticmethod
    @transaction.atomic
    def load_users_init(owner_email: str = "admin@gmail.com", proofs: bool = True):
        """
        Main method to seed users into the system.
        
        This method is wrapped in a database transaction to ensure that either all 
        users are created or none are, maintaining database integrity.

        Args:
            owner_email (str): The primary administrator email address. Defaults to "admin@gmail.com".
            proofs (bool): If True, creates additional sample sellers for testing purposes.
        """
        
        # 1. Security Validation
        # Prevents running production-like setups with the default "admin@gmail.com" email.
        if not proofs and owner_email == "admin@gmail.com":
            logger.error("Error: A valid production email is required for the owner.")
            return
            
        # 2. Define Superuser Accounts
        # These accounts are granted full system access (staff and superuser status).
        admins = [
            {"email": owner_email, "first": "Admin", "last": "Principal"},
            {"email": UserInit.EMAIL_DEV, "first": "Lucas", "last": "Dev"},
        ]

        for admin_data in admins:
            user, created = User.objects.get_or_create(
                email=admin_data["email"],
                defaults={
                    "password": make_password(UserInit.PW_DEFAULT),
                    "first_name": admin_data["first"],
                    "last_name": admin_data["last"],
                    "is_staff": True,
                    "is_superuser": True,
                    "role": 'admin',  # Custom role field
                }
            )
            if created:
                logger.debug(f"[USER APP] Superuser created: {user.email}")

        # 3. Define Standard/Test Accounts
        # Includes a default local buyer and optional sellers for demonstration.
        test_users = [
            {
                "email": UserInit.EMAIL_DEF_CLIENT, 
                "first": "Comprador", 
                "last": "Local", 
                "role": "buyer"
            }
        ]
        
        # Add extra sample accounts if 'proofs' is enabled
        if proofs:
            test_users.extend([
                {"email": "seller1@gmail.com", "first": "Vendedor", "last": "Uno", "role": "seller"},
                {"email": "seller2@gmail.com", "first": "Vendedor", "last": "Dos", "role": "seller"},
            ])

        for u_data in test_users:
            user, created = User.objects.get_or_create(
                email=u_data["email"],
                defaults={
                    "password": make_password(UserInit.PW_DEFAULT),
                    "first_name": u_data["first"],
                    "last_name": u_data["last"],
                    "role": u_data.get("role", "buyer"),
                }
            )
            if created:
                logger.debug(f"[USER APP] User created: {user.email}")


class StoreInit:
    """
    Service class to handle the initial setup and data seeding for the Store.
    This includes creating the main Store instance, default images, and social media links.
    """

    @staticmethod
    def load_store_init(data: dict):
        """
        Main entry point for store initialization. 
        Creates the unique Store record and triggers secondary data seeding (Images/Social Media).

        Args:
            data (dict): A dictionary containing 'name' and 'defaults' for Store creation.
        """
        # Create or retrieve the unique Store instance using the provided configuration
        store, created = Store.objects.get_or_create(
            name=data["name"],
            defaults=data["defaults"]
        )

        if created:
            logger.debug(f"[STORE APP] Store '{store.name}' created successfully.")
        else:
            logger.debug("[STORE APP] Script already executed. load_store_init aborted.")
            logger.debug(f"[STORE APP] Store '{store.name}' already exists.")
            return
        
        # Initial Placeholder Assets
        list_headers = [
            "https://redragon.es/content/uploads/2021/10/HEROS-S129W-BA.jpg",
            "https://sigmatiendas.com/cdn/shop/files/Logitech_banner_product_page_v2.jpg?v=1711139345&width=2800",
            "https://assets2.razerzone.com/images/pnx.assets/4b93db266e7ee65c3a25a5ae582ed586/razer-affiliate-hero-mobile.jpg"
        ]
        
        list_banners = [
            "https://www.techgames.com.mx/wp-content/uploads/2021/10/Logitech-G-y-Riot-Games-LOL.jpg",
            "https://redragonshop.com/cdn/shop/files/referal-candy-banner-m.png?v=1709540400"
        ]

        # Trigger internal methods to seed related data
        StoreInit._create_initial_store_images(list_headers, StoreImage.ImageType.HEADER, store)
        StoreInit._create_initial_store_images(list_banners, StoreImage.ImageType.BANNER, store)
        StoreInit._create_social_media_defaults(store)

    @staticmethod
    def _create_social_media_defaults(store: Store):
        """
        Creates a default set of social media profiles for the given store.

        Args:
            store (Store): The Store instance to link the profiles to.
        """
        default_platforms = {
            SocialMedia.PlatformEnum.GG: "https://google.com/",
            SocialMedia.PlatformEnum.IG: "https://instagram.com/",
            SocialMedia.PlatformEnum.FB: "https://facebook.com/",
            SocialMedia.PlatformEnum.TT: "https://www.tiktok.com",
            SocialMedia.PlatformEnum.TW: "https://x.com/home",
            SocialMedia.PlatformEnum.YT: "https://www.youtube.com",
            SocialMedia.PlatformEnum.GM: "https://google.com/maps",
        }
        
        for plat, url in default_platforms.items():
            obj, created = SocialMedia.objects.get_or_create(
                store=store, 
                platform=plat, 
                defaults={'url': url, 'is_active': True}
            )
            if created:
                logger.debug(f'[STORE APP] Social Media {obj.get_platform_display()} created.')

    @staticmethod
    def _create_initial_store_images(list_urls: list, image_type: str, store: Store):
        """
        Iterates through a list of URLs and creates StoreImage records.
        Sets the first image of the list as the 'main_image'.

        Args:
            list_urls (list): List of strings (Image URLs).
            image_type (str): Type of image (e.g., 'header', 'banner').
            store (Store): The Store instance to link the images to.
        """
        for index, url in enumerate(list_urls):
            # Only the first image in the list is marked as 'main_image' by default
            is_main = (index == 0)
            
            imagen, created = StoreImage.objects.get_or_create(
                store=store, 
                image_url=url, 
                image_type=image_type,
                defaults={'main_image': is_main, 'available': True}
            )
            if created:
                logger.debug(f"[STORE APP] Added {image_type}: {url} (Is Main: {is_main})")


""" 
def load_data(model_class, data):
    # Carga datos en un modelo de Django usando get_or_create.
    # Args:
    #    model_class (Model): Clase del modelo en el que se cargarán los datos.
    #    data (list): Lista de diccionarios con los datos a cargar.
    
    for item in data:
        objeto, created = model_class.objects.get_or_create(**item)
        if created:
            print(f'Se creó correctamente: {objeto}')
        else:
            print(f'Ya existía: {objeto}')

def load_orders_init():
    # Este metodo ya no se utiliza porque se movió a un signals en orders/signals/deafaults.py 
    from orders.models import StatusOrder, PaymentMethod, ShipmentMethod
    
    # Datos a cargar
    data_order_status = [
        {'name': 'Cancelado', 'description': 'El envío fue cancelado.'},
        {'name': 'Pago a Confirmar', 'description': 'Se deberá confirmar el ingreso a la cuenta bancaria.'},
        {'name': 'Pago Confirmado', 'description': 'Una vez confirmado el pago.'},
        {'name': 'Pendiente de Retiro', 'description': 'Espera a ser retirado en Local.'},
        {'name': 'Preparando Envío', 'description': 'Tu pedido esta siendo preparado.'},
        {'name': 'En Camino', 'description': 'Tu pedido partió al domicilio indicado.'},
        {'name': 'Completado', 'description': 'Pedido Recibido.'},
        {'name': 'Devolución', 'description': 'Estado para pedidos devueltos.'},
        {'name': 'Rechazado', 'description': 'Rechazado por falta de Stock o Fraude.'},
    ]

    data_payment_methods = [
        {'name': 'Efectivo o Pago en Local', 'description': 'Completa el pago retirando por el local. (Solo entregas en el día)', 'is_active': True, 'time': 12},
        {'name': 'Transferencia Bancaria', 'description': 'Precio especial de contado por Transferencia directa.', 'is_active': True, 'time': 2},
        {'name': 'Tarjeta Crédito o Debito', 'description': 'Consultar promociones con tarjeta.', 'is_active': False, 'time': 2},
        {'name': 'USD Theter', 'description': 'Precios especiales por pago en criptomoneda.', 'is_active': False, 'time': 2},
    ]

    data_envio_methods = [
        {'name': 'Retiro en Local', 'description': 'Retiras en nuestro local', 'is_active': True, 'price': 0},
        {'name': 'Dentro de Circunvalación', 'description': 'Envío dentro del anillo de Córdoba', 'is_active': False, 'price': 1000.00},
        {'name': 'Fuera de Circunvalación', 'description': 'Envío fuera del anillo de Córdoba', 'is_active': False, 'price': 1500.00},
        {'name': 'Puntos de Retiro Correo', 'description': 'Envío para otras provincias', 'is_active': False, 'price': 3000.00},
    ]

    # Llamadas a la función genérica
    load_data(StatusOrder, data_order_status)
    load_data(PaymentMethod, data_payment_methods)
    load_data(ShipmentMethod, data_envio_methods)
"""