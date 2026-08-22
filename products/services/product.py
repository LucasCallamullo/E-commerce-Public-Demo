# products/services/read.py
from typing import Optional
from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramSimilarity
from django.db import transaction
from django.db.models import F, Q, QuerySet
from django.db.models.functions import Coalesce
from decimal import Decimal, ROUND_HALF_UP

# --- Soft Dependencies (Intento de importación opcional) ---
try:
    from analytics.services.stock_services import FinancialStockService
    HAS_ANALYTICS = True
except (ImportError, ModuleNotFoundError):
    FinancialStockService = None
    HAS_ANALYTICS = False

try:
    from audit.services.audit_service import AuditService
    HAS_AUDIT = True
except (ImportError, ModuleNotFoundError):
    AuditService = None
    HAS_AUDIT = False

# Core app
from core.clients.favorites_client import FavoritesClient
from core.utils.utils_db import model_optimized_update

# Product app
from products.models.product import Product
from products.services.product_images import ProductImageService

import logging
logger = logging.getLogger(__name__)

# 547 Lineas
class ProductService:
    
    ORDER_BY = ('price_ars', 'id')
    
    # Fields Used for Update
    FIELDS_UPDATE = (
        # Realmente no haría falta traerlos segun tests
        # 'slug', 'normalized_name',    --> solo se modificar en memoria
        # 'category_id', 'subcategory_id', 'brand_id', --> se traen con el select_related
        'id', 'name', 'available', 'stock', 'description',  'updated_at', 'main_image',
        'price_ars', 'discount_ars', 'cost_avg_ars', 'price_list',
        'price_usd', 'discount_usd', 'is_linked_prices', 'sku',
        'category__id', 'category__name', 'category__is_default',
        'subcategory__id', 'subcategory__name', 'subcategory__category_id',
        'brand__id', 'brand__name', 'brand__is_default',
    )

    # this is use for a product_detail view
    PRODUCT_FIELDS_DETAIL_VIEW = (
        'id', 'slug', 'name', 'price_ars', 'discount_ars', 'price_list', 
        'available', 'stock', 'description', 'updated_at', 'main_image',
        'category__id', 'category__slug', 'category__name', 'category__is_default',
        'subcategory__id', 'subcategory__slug', 'subcategory__name', 
        'brand__id', 'brand__slug', 'brand__name', 'brand__is_default',
    )

    # this is use for a product_list.html / views.product_lsit
    VALUES_CARDS_LIST = (
        'id', 'name', 'price_ars', 'price_list', 'available', 'stock',
        'discount_ars', 'updated_at', 'main_image', 'slug',
    )
    
    # this use in dashboard products section
    VALUES_DASHBOARD_PRODUCTS = (
        'id', 'name', 'main_image', 'available', 'stock', 
        'price_ars', 'discount_ars', 'updated_at',
    )
    # this is call on every modal open it to extra values
    DASHBOARD_DETAIL = (
        'id', 'description', 'sku', 'price_list', 'cost_avg_ars', 
        'price_usd', 'discount_usd', 'is_linked_prices',
    )
    
    PRODUCT_CART_FIELDS = (
        'id', 'slug', 'name', 'price_ars', 'discount_ars',
        'main_image', 'stock', 'available'
    )
    
    @classmethod
    def get_product_for_cart(cls, *, product_id: int) -> Optional[Product]:
        return Product.objects.filter(id=product_id).only(*cls.PRODUCT_CART_FIELDS).first()

    @classmethod
    def get_dashboard_detail(cls, *, product_id: int) -> Optional[dict]:
        """
        Retrieves specific product data for administrative display purposes.

        Returns:
            dict | None: A dictionary containing 'id' and 'description' if found,
                otherwise None.
        """
        return (
            Product.objects.filter(id=product_id)
            .values(*cls.DASHBOARD_DETAIL).first()
        )

    @classmethod
    def get_home_data(cls, *, user = None) -> dict[str, list[dict]]:
        """
        Retrieves and categorizes product data for the home screen display.

        This method performs a single optimized database hit to fetch all active 
        products with stock, then processes them in memory to separate discounted 
        items from the general catalog. It also marks products as favorites if 
        a user is provided.

        Args:
            user (User, optional): The authenticated user instance to check for 
                favorite products. Defaults to None.

        Returns:
            dict[str, list[dict]]: A dictionary containing two keys:
                - 'offers': List of products with a discount greater than 0.
                - 'products': The full list of available products.
        """
        # Get the set of IDs that the user has marked as favorites
        favorites_ids = FavoritesClient.get_user_favorites_ids(user)
        # Unified Query: Fetch available products with stock and valid categorization
        qs = (
            Product.objects.select_related('category', 'subcategory')
            .filter(
                available=True, stock__gt=0, 
                category__is_default=False,
                subcategory__isnull=False
            ) # [:100]    # limita a 100 la query
            .filter(Q(discount_ars__gt=0) | Q(discount_ars=0))
            .distinct()
        )
    
        # Convert QuerySet to list of dictionaries and inject 'is_favorite' flag
        products = cls._add_products_flag(list(
            cls._prepare_qs_values(qs=qs, values=cls.VALUES_CARDS_LIST, sort_order=cls.ORDER_BY)
        ), favorites_ids)
        
        # Split data in memory to avoid multiple database round-trips
        return {
            "offers": [p for p in products if p['discount_ars'] > 0],
            "products": products
        }
    
    
    
    @classmethod
    def for_detail(cls, *, entity_id: int, entity_slug: str) -> Product:
        """
        Retrieve a single product optimized for the public detail page.

        Args:
            entity_id (int): Product ID.
            entity_slug (str): Product slug.

        Returns:
            Product: Product model instance or None.
        """
        return cls._get_product(
            entity_id=entity_id,
            entity_slug=entity_slug,
            values=cls.PRODUCT_FIELDS_DETAIL_VIEW
        )
    
    
    @classmethod
    def for_favorites_list(cls, *, user=None) -> list[dict]:

        favorites_ids = FavoritesClient.get_user_favorites_ids(user)
        qs = FavoritesClient.get_qs_favs_products(
            user, 
            favorites_ids=favorites_ids
        )
        # evaluamos el qs deja de ser lazy para agregar más data en el siguiente metodo
        products = list(cls._prepare_qs_values(
            qs=qs, values=cls.VALUES_CARDS_LIST, sort_order=cls.ORDER_BY
        ))
        return cls._add_products_flag(products, favorites_ids)

    @classmethod
    def for_card_list(cls, *, user=None) -> list[dict]:
        """
        Return products formatted for card listing.
        Adds `is_favorited` if user is provided.
        """
        if not user:
            return []
        
        qs = Product.objects.all()
        favorites_ids = FavoritesClient.get_user_favorites_ids(user)

        # evaluamos el qs deja de ser lazy para agregar más data en el siguiente metodo
        products = list(cls._prepare_qs_values(
            qs=qs, values=cls.VALUES_CARDS_LIST, sort_order=cls.ORDER_BY
        ))
        
        return cls._add_products_flag(products, favorites_ids)
    
    @classmethod
    def qs_for_card_list(cls, *, filters: dict) -> QuerySet:
        return cls._get_qs_products_filters(
            filters=filters, values=cls.VALUES_CARDS_LIST, sorted_by=cls.ORDER_BY
        )
        
    @classmethod
    def qs_for_dashboard(cls, *, filters: dict) -> QuerySet:
        """ this is only for dashboard admin, especifics values """
        return cls._get_qs_products_filters(
            filters=filters, values=cls.VALUES_DASHBOARD_PRODUCTS, sorted_by=('name', 'id')
        )

    @staticmethod
    def serializer_list_add_flags(*, products: list[dict], user=None) -> list[dict]:
        # solo buscar en favorites client si hay user...
        favorites_ids = FavoritesClient.get_user_favorites_ids(user) if user else set() 
        return ProductService._add_products_flag(products, favorites_ids)
    
    # ---------------- PRIVATE HELPERS (Internal logic) ---
    
    @classmethod
    def _get_product(
        cls,
        entity_id: int | None = None,
        entity_slug: str | None = None,
        values: tuple[str, ...] = ("id", "name"),
    ) -> Optional[Product]:
        """
        Internal helper to retrieve a single product with selected fields.
        
        Args:
            entity_id (int | None): Product ID.
            entity_slug (str | None): Product slug.
            values (tuple[str, ...]): Fields to load using `.only()`.

        Returns:
            Product: Product model instance.
        """
        # Guard clause: Ensure at least one identifier is provided
        if not entity_slug and not entity_id:
            return None
        
        # Initialize optimized QuerySet
        qs = (
            Product.objects
            .select_related("category", "subcategory", "brand")
            .only(*values)
        )
        
        if entity_id:
            qs = qs.filter(id=entity_id)

        if entity_slug:
            qs = qs.filter(slug=entity_slug)

        return qs.first()
    
    @classmethod
    def _get_qs_products_filters(cls, filters: dict, values: tuple, sorted_by: tuple) -> QuerySet:
        """
        Advanced multi-parameter filter for the Product catalog.
        
        Implements a two-tier search strategy:
        1. PostgreSQL Full Text Search (FTS) with Rank for high-performance exact/prefix matching.
        2. Trigram Similarity fallback for fuzzy matching (typo tolerance) when FTS yields no results.
        
        Args:
            filters (dict): Search parameters including 'category', 'brand', 'stock', 
                            'query' (user search), and 'get_all' (bypasses availability).
            values (tuple): Model fields to be included in the final dictionary output.
            sorted_by (tuple): Default sorting fields (overridden if a search query is present).
        
        Returns:
            QuerySet: A prepared QuerySet of dictionaries based on the '_prepare_qs_values' mapping.
        """
        get_all = filters.get('get_all', False)      # True || False
        available = filters.get('available', True)   # True || False
        category_id = filters.get('category')        # ID || None
        subcategory_id = filters.get('subcategory')  # ID || 'is_null' || None
        brand_id = filters.get('brand')              # ID || None
        query = filters.get('query', '')             # Str
        top_query = filters.get('top_query', '')     # Str
        stock = filters.get('stock', 0)              # int

        # Base QuerySet: Check global availability unless 'get_all' is specified
        qs = Product.objects.all() if get_all else Product.objects.filter(available=available)
        
        if stock:
            qs = qs.filter(stock__gt=stock)

        if category_id:
            qs = qs.filter(category_id=category_id)
            
        if subcategory_id:
            if subcategory_id == 'is_null':
                qs = qs.filter(subcategory__isnull=True)
            else:
                qs = qs.filter(subcategory_id=subcategory_id)

        if brand_id:
            qs = qs.filter(brand_id=brand_id)
        
        # --- Search Logic (FTS & Trigram Fallback) ---
        if query or top_query:
            chain = f"{query} {top_query}".strip()
            words = chain.split()
            
            # 1. Intentar FTS Primero (Rápido)
            fts_filter = Q()
            fts_rank_expr = None
            for word in words:
                # En caso de querer usar el AND descomentar pero realmente vamos a usar el OR
                # fts_filter &= Q(search_vector=SearchQuery(f"{word}:*", search_type='raw'))
                fts_filter |= Q(search_vector=SearchQuery(f"{word}:*", search_type='raw'))
                
                # Nota: Usamos &= (AND) para que sea muy específico
                r = SearchRank(F('search_vector'), SearchQuery(f"{word}:*", search_type='raw'))
                
                # FTS rank expression
                if fts_rank_expr is None:
                    fts_rank_expr = r
                else:
                    fts_rank_expr += r

            fts_qs = qs.filter(fts_filter).annotate(rank=fts_rank_expr).order_by('-rank')

            # Si FTS encontró resultados suficientes, devolvemos eso
            if fts_qs.exists():
                qs = fts_qs
                logger.debug('[PRODUCTS FILTER] ONLY FTS')
                
            elif len(chain) >= 3:
                # 2. Si FTS falló (0 resultados), ejecutamos Trigram (Lento pero tolerante)
                trigram_filter = Q()
                trigram_rank_expr = None
                
                for word in words:
                    trigram_filter |= Q(normalized_name__icontains=word)
                    
                    # Trigram similarity ranking
                    t = TrigramSimilarity('normalized_name', word)
                    if trigram_rank_expr is None:
                        trigram_rank_expr = t
                    else:
                        trigram_rank_expr += t
                
                qs = qs.filter(trigram_filter).annotate(
                    rank=Coalesce(trigram_rank_expr, 0.0)
                ).order_by('-rank')
                
                logger.debug('[PRODUCTS FILTER] ONLY TRIGRAM')
    
            # Override default sorting when searching to prioritize Rank/Similarity
            sorted_by = None
        
        return cls._prepare_qs_values(qs=qs, values=values, sort_order=sorted_by)
    
    
    @staticmethod
    def _prepare_qs_values(*, qs: QuerySet, values: tuple, sort_order: tuple = None) -> QuerySet:
        """
        Transforms a Product QuerySet into a values-based QuerySet (dictionaries).
        
        It flattens relational IDs for Brand, Category, and Subcategory to ensure 
        consistent key naming in the resulting dictionaries.

        Args:
            qs (QuerySet): The initial Product QuerySet.
            values (tuple): The specific fields to retrieve from the Product model.
            sort_order (tuple | None): Optional fields to define the sort sequence.

        Returns:
            QuerySet: A QuerySet yielding dictionaries instead of model instances.
        """
        optimized_qs = (
            qs.values(*values)
            .annotate(
                brand_id=F("brand__id"),
                category_id=F("category__id"),
                subcategory_id=F("subcategory__id"),
            )
        )
        if sort_order:
            return optimized_qs.order_by(*sort_order)
        
        return optimized_qs
        
    @staticmethod
    def _add_products_flag(products: list[dict], favorites_ids: set[int] = None) -> list[dict]:
        """
        Add `is_favorited` boolean to each product.
        Add `price_discount` decimal representing price minus discount percentage.
        """
        for p in products:
            # Favorited flag
            p['is_favorited'] = p['id'] in favorites_ids if favorites_ids else False

            # Discounted price
            discount = Decimal(p.get('discount_ars', 0))
            try:
                price = Decimal(p['price_ars'])
                if discount != 0:
                    p['price_discount'] = (
                        price * (Decimal('1') - discount / Decimal('100'))
                    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                else:
                    p['price_discount'] = price
            except (ValueError, TypeError, KeyError):
                p['price_discount'] = p.get('price_ars', 0)

        return products

    # ---------------- WRITE OPERATIONS (Business Logic, Updates, Creation) ---
    
    @classmethod
    def get_product_for_update(cls, *, entity_id: int) -> Optional[Product]:
        """
        Retrieve a single product optimized for the API Patch Request.
        """
        return cls._get_product(entity_id=entity_id, values=cls.FIELDS_UPDATE)
    
    @classmethod
    @transaction.atomic
    def handle_create(cls, *, payload: dict, audit_data: dict) -> Product:
        """
        Orchestrates the product creation lifecycle, including financial initialization and auditing.

        This method performs pre-persistence data transformation (initial WAC calculation), 
        persists the product instance, and triggers secondary events for inventory analytics 
        and forensic traceability.

        Args:
            payload (dict): Validated product data. Expected to contain volatile fields 
                such as 'stock_increment' and 'unit_cost'.
            audit_data (dict): Metadata for traceability, including 'user' and 'ip'.
        """
        # Transforms stock_increment and unit_cost into final stock and cost values
        payload = cls._get_payload_valid(product=None, payload=payload)
        
        created = Product.objects.create(**payload)
        
        # Financial snapshot: Records initial cost and price state
        cls._handle_analytics_service(instance=created, user=audit_data.get('user'))
        
        # Forensic logging: Records the creation event in the centralized audit log
        cls._handle_audit_service(instance=created, payload=payload, data=audit_data, is_create=True)
    
    @classmethod
    @transaction.atomic
    def handle_update(cls, *, instance: Product, payload: dict, audit_data: dict) -> Product:
        """
        Manages the complete update lifecycle of an existing product.

        Coordinates primary image promotion, financial re-valuation (Weighted Average Cost), 
        optimized database persistence, and notification of optional external services.

        Args:
            instance (Product): The existing product instance to update.
            validated_data (dict): The cleaned data from the serializer.
            audit_data (dict): Metadata for traceability (user, ip, old_state).
        """
        #Image Management: Delegates main image logic and URL mapping.
        payload = cls._update_main_image(instance=instance, payload=payload)
        
        # calculates new Weighted Average Cost (WAC) and clean payload to get 'stock' and 'cost'
        payload = cls._get_payload_valid(product=instance, payload=payload)
        
        # Data Integrity: Leverages SlufFieldMixin logic (auto-slugging) and DB-level Search Vectors.
        # Persistence: Updates the instance in a atomic transaction.
        updated = model_optimized_update(instance=instance, validated_data=payload)
        
        # Financial tracking: persists price/cost history if the analytics module is active
        cls._handle_analytics_service(instance=updated, user=audit_data.get('user'))
        
        # Detailed auditing: logs specific changes (before/after) for security tracking
        cls._handle_audit_service(instance=updated, payload=payload, data=audit_data, is_create=False)

        return updated
    
    @staticmethod
    def _handle_analytics_service(instance: Product | None, user = None) -> None:
        """
        Integration hook for the Finance & Inventory Analytics module.

        If the Analytics application is present, it captures a snapshot of the product's 
        current financial state to power profitability and valuation reports.
        """
        if not HAS_ANALYTICS:
            logger.debug("Analytics app not found. Skipping stock entry registration.")
            return
        
        FinancialStockService.register_stock_entry(product=instance, user=user)
 
    @staticmethod
    def _handle_audit_service(instance: Product, payload: dict, data: dict, is_create: bool) -> None:
        """
        Integration hook for the Centralized Audit & Security module.

        Logs security events and data modifications. Decouples auditing logic 
        from the core product business logic through a conditional feature toggle.
        """
        if not HAS_AUDIT:
            logger.debug("Audit app not found. Skipping audit entry registration.")
            return 
        
        AuditService.logs_product(product=instance, data=data, payload=payload, is_create=is_create)

    @staticmethod
    def _get_payload_valid(*, product: Product | None, payload: dict) -> dict:
        """
        Calculates the new Weighted Average Cost (WAC) and total stock.
        
        This is a data transformation method. It should be called BEFORE 
        saving the product to the database.
        
        Args:
            product: Existing instance (None if creating).
            payload: Validated data from serializer/request.
            
        Returns:
            dict: The payload enriched with calculated 'stock' and 'cost'.
        """
        # Remove fields that don't exist in the Product Model
        qty_to_add = payload.pop('stock_increment', 0) 
        unit_cost = payload.pop('cost_unit', None)
        
        # If there is no increase in stock or the purchase cost is missing,
        # we return the payload as is (no WAC calculation to perform)
        if not qty_to_add or unit_cost is None:
            return payload
        
        # CREATE / POST    
        # Creation: The initial average cost is simply the unit cost
        total_value = Decimal(qty_to_add) * Decimal(unit_cost)
        new_total_stock = qty_to_add
        
        # UPDATE / PATCH
        if product:
            # Existing Product: We average with what is already in the DB
            # Calcular costo promedio ponderado
            # Fórmula: ((Stock actual * Costo actual) + (Nuevo stock * Nuevo costo)) / Stock Total
            total_value += (product.stock * product.cost_avg_ars)
            new_total_stock += product.stock
            
        # Cálculo final del WAC
        new_avg_cost = (total_value / new_total_stock 
            if new_total_stock > 0 else Decimal(unit_cost)) 
        
        # Update the DTO (payload)
        payload['stock'] = new_total_stock
        payload['cost_avg_ars'] = new_avg_cost.quantize(Decimal('0.01'))
        
        return payload
    
    @staticmethod
    def _update_main_image(*, instance: Product, payload: dict) -> dict:
        """
        Orchestrates the primary image update process during a product modification.
        """
        # Validation: Checks if a 'main_image' ID was provided in the request.
        main_image_id = payload.get('main_image', None)
        if not main_image_id:
            payload.pop('main_image', None)
            return payload
        
        # Data Isolation: Fetches only the images belonging to the current product to 
        # prevent unauthorized assignment of images from other products.
        new_image = ProductImageService.get_image_by_id(
            product_id=instance.id, image_id=main_image_id
        )
        
        if new_image:
            # Change Detection: Only triggers the database-heavy 'main_image' promotion 
            # logic if the target image URL differs from the current one.
            if new_image.image_url != instance.main_image:
                ProductImageService.handle_update_main_image(image=new_image)

            # Data Transformation: Replaces the Image ID in 'validated_data' with its 
            # corresponding URL string to match the Product model's schema requirements.
            payload['main_image'] = new_image.image_url 
        else:
            payload['main_image'] = instance.main_image
            
        return payload
