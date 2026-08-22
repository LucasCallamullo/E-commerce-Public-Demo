# from django.conf import settings
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.core.management.base import BaseCommand
from products.models.product import Product

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to execute maintenance tasks that are difficult 
    to automate in environments such as Railway or during initial deployment.
    """
    help = "Executes scripts for name normalization, search vector updates, and store seeding."
    
    def handle(self, *args, **kwargs):
        """
        Entry point for the command. Uncomment the required function 
        to execute the specific maintenance or update logic.
        """
        # update_normalized_names()
        # update_vector_progress()
        
        # Ensures default social media profiles are initialized for the store
        # update_new_social_media()
        # update_audit_app()
        # update_cost_avg_init()
        pass
    
    
def update_cost_avg_init():
    """
    Initializes financial data for all products after the introduction of 
    Weighted Average Cost (WAC) and multi-currency tracking.
    
    Tasks:
    1. Updates the global Store exchange rate to a baseline (1400 ARS/USD).
    2. Creates an entry in ExchangeRateHistory for auditing purposes.
    3. Bulk updates all products to set an initial 'cost_avg_ars' (80% of current price)
       and recalculates 'price_usd' based on the new rate.
    
    Performance:
    - Uses .iterator() and .only() to minimize RAM consumption.
    - Implements .bulk_update() in chunks of 100 to optimize database I/O.
    """
    from home.models.store import Store
    from analytics.models import ExchangeRateHistory
    
    with transaction.atomic():

        # 1. Actualizar Tienda
        store = Store.objects.select_for_update().get(id=1)
        new_usd = Decimal('1400.00')
        store.usd_exchange_rate = new_usd
        store.save()
        
        # 2. Crear Historial
        ExchangeRateHistory.objects.create(
            store=store,
            rate=new_usd
        )
        
        # 3. Procesar Productos de forma eficiente
        # Con .iterator(): La RAM se llena solo con la cantidad de objetos 
        # definida en el chunk_size. Si traes 1000, ocupas RAM por esos 1000. 
        # Al pasar al 1001, Django "descarta" los anteriores de la memoria y 
        # trae los nuevos. Es una ocupación temporal y controlada.
        # Trae de a 1000 registros por cada viaje a la base de datos
        products = Product.objects.all().only(
            'id', 'price_ars', 'price_usd', 'cost_avg_ars'
        ).iterator(chunk_size=1000)
        
        updated_products = []
        for p in products:
            # Calcular costo ficticio (80% del precio actual)
            # Usamos Decimal para evitar errores de precisión
            new_cost = p.price_ars * Decimal('0.8')
            
            # Actualizar campos
            p.cost_avg_ars = new_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Calcular precio USD basado en la nueva tasa
            if p.price_ars > 0:
                p.price_usd = (p.price_ars / new_usd).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                p.price_usd = Decimal('0.00')
            
            updated_products.append(p)
            
            # Guardamos en baches de 100 para no saturar la transacción
            if len(updated_products) >= 100:
                Product.objects.bulk_update(updated_products, ['cost_avg_ars', 'price_usd'])
                updated_products = []

        # Guardar los que sobraron
        if updated_products:
            Product.objects.bulk_update(updated_products, ['cost_avg_ars', 'price_usd'])

        print("Actualización masiva completada con éxito.")

    
def update_audit_app():
    """
    Migrates existing AuditLog entries to a generic relation structure.
    
    Purpose:
    Updates logs that were previously hardcoded to a 'Product' ForeignKey, 
    populating 'object_id' and 'object_type' to support future polymorphism 
    (logging other models like Categories or Expenses).
    
    Optimization:
    - Uses .select_related('product') to avoid N+1 queries.
    - Uses save(update_fields=...) to prevent triggering unnecessary signals 
      or updating timestamps on other fields.
    """
    from audit.models import AuditLog
    logs_to_update = AuditLog.objects.select_related('product').filter(product__isnull=False)

    count = logs_to_update.count()
    logger.info(f"Iniciando migración de {count} logs...")

    # Usamos una transacción para que sea rápido y seguro
    with transaction.atomic():
        for log in logs_to_update:
            product = log.product
            log.object_id = str(product.id)
            log.object_type = product._meta.label_lower
            # Guardamos solo los campos que cambiaron para evitar efectos secundarios
            log.save(update_fields=['object_id', 'object_type'])
            logger.debug('Log Object ID: %s | Object Type: %s', log.object_id, log.object_type)

    logger.info("Migración completada con éxito.")
    
    
def update_vector_progress():
    """
    Manually updates the PostgreSQL SearchVector for the Product model.
    
    NOTE: This process is now automated via a Database Trigger (see core migration 0003).
    This function serves as a fallback or "warm-up" script to force an update 
    on records that existed before the trigger was implemented.
    """
    from django.contrib.postgres.search import SearchVector
    
    # Ensure all product names are normalized before vectorizing
    update_normalized_names()
    
    logger.info("Updating SearchVectors via Django ORM...")
    
    # Explicitly calculate the search_vector using the normalized_name field.
    # Weight 'A' gives this field the highest priority in search results.
    Product.objects.update(search_vector=SearchVector('normalized_name', weight='A'))
    
    # Console verification loop
    products = Product.objects.all().only('id', 'name', 'normalized_name', 'search_vector')
    for p in products:
        print(f"Vector Check -> {p.normalized_name}: {p.search_vector}")


def update_normalized_names():
    """
    Normalizes product names and performs a bulk database update.
    
    This function uses 'bulk_update' to optimize performance by executing a 
    single SQL query instead of calling .save() for each individual product.
    
    TECHNICAL NOTE: 
    Using bulk_update bypasses Django signals (post_save), but since 
    a PostgreSQL Trigger is used (Migration 0003), the 'search_vector' 
    will still be updated at the database level.
    """
    from core.utils.utils_parsers import normalize_or_None
    
    products = Product.objects.all()
    if not products.exists():
        logger.info("No products found to normalize.")
        return

    for product in products:
        # Generate a clean version of the name (lowercase, no accents, etc.)
        product.normalized_name = normalize_or_None(product.name)
        print(f"Processing: {product.name} -> {product.normalized_name}")
        
    # Execute an atomic batch update for the 'normalized_name' field.
    # This is significantly faster for large datasets.
    Product.objects.bulk_update(products, ['normalized_name'])
    logger.info(f"Successfully normalized {len(products)} products.")
    
    
def update_new_social_media():
    """
    Utility script to ensure all default social media profiles exist for the main store.
    
    Purpose:
        To be executed during development or after migrations when new 
        social media platforms are added to the PlatformEnum.
        
    Note:
        This function is idempotent; it checks for existing records before 
        creating new ones via 'StoreInit._create_social_media_defaults'.
    """
    from ....home.management.commands.init_store_users import StoreInit
    from home.models import Store
    
    # We fetch the primary store instance. 
    # In this single-store architecture, ID 1 is the default target.
    store = Store.objects.filter(id=1).first()
    
    if store:
        StoreInit._create_social_media_defaults(store=store)
        logger.debug(f"Social media defaults verified/created for: {store.name}")
    else:
        logger.warning("Warning: Store with ID 1 not found. Skipping social media defaults.")