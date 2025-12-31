# products/services/read.py
from typing import Any
from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramSimilarity
# from django.db.models import F, Q, FloatField, Case, When, Value, QuerySet, Count
from django.db.models import F, Q, QuerySet
from django.db.models.functions import Coalesce
from decimal import Decimal, ROUND_HALF_UP


from products.models.product import Product

from core.clients.favorites_client import FavoritesClient
from core.utils.utils_basic import valid_id_or_None

import logging
logger = logging.getLogger(__name__)

class ProductService:
    """
    Read-only service for product card listings.
    """
    
    # CONST TUPLES FILTERS
    # para desempaquetar la tupla como argumentos para .only().
    PRODUCT_FIELDS_UPDATE = (
        'name', 'slug', 'normalized_name', 'price', 'price_list', 'available', 'stock',
        'description', 'discount', 'updated_at', 'main_image',
        'subcategory__id', 'subcategory__name',
        'subcategory__category__id', 'subcategory__category__name',
        # 'category__id', 'category__name', 
        'brand__id', 'brand__name'
    )

    # this is use for a product_detail view
    PRODUCT_FIELDS_DETAIL_VIEW = (
        'id', 'slug', 'name', 'price', 'price_list', 'available', 'stock',
        'description', 'discount', 'updated_at', 'main_image',
        'subcategory__slug', 'subcategory__name', 'subcategory__is_default',
        'subcategory__category__slug', 'subcategory__category__name', 'subcategory__category__is_default',
        # 'category__slug', 'category__name', 'category__is_default',
        'brand__slug', 'brand__name', 'brand__is_default'
    )

    # this is use for a product_list.html / views.product_lsit
    VALUES_CARDS_LIST = (
        'id', 'slug', 'name', 'price', 'price_list', 'available', 'stock',
        'discount', 'updated_at', 'main_image'
    )
    
    # this use in dashboard products section
    VALUES_DASHBOARD_PRODUCTS = (
        'id', 'name', 'price', 'price_list', 'available', 'stock',
        'description', 'discount', 'updated_at', 'main_image'
    )

    
    @staticmethod
    def for_detail(*, entity_id: int, entity_slug: str) -> Product:
        """
        Retrieve a single product optimized for the public detail page.

        Args:
            entity_id (int): Product ID.
            entity_slug (str): Product slug.

        Returns:
            Product: Product model instance.

        Raises:
            Product.DoesNotExist: If the product does not exist.
        """
        return ProductService._get_detail(
            entity_id=entity_id,
            entity_slug=entity_slug,
            values=ProductService.PRODUCT_FIELDS_DETAIL_VIEW
        )
        
    @staticmethod
    def for_patch(*, entity_id: int) -> Product:
        """
        Retrieve a single product optimized for the public detail page.

        Args:
            entity_id (int): Product ID.
            entity_slug (str): Product slug.

        Returns:
            Product: Product model instance.

        Raises:
            Product.DoesNotExist: If the product does not exist.
        """
        return ProductService._get_detail(
            entity_id=entity_id,
            values=ProductService.PRODUCT_FIELDS_UPDATE
        )
    
    @staticmethod
    def for_home(*, user=None) -> list[dict]:
        favorites_ids = FavoritesClient.get_user_favorites_ids(user)
        
        qs = Product.objects.select_related(
            'subcategory__category'
            ).filter(
                subcategory__category__is_default=False,
                available=True,
                stock__gt=0
            )   # [:100]    # limita a 100 la query
        products = ProductService._product_list(qs, ProductService.VALUES_CARDS_LIST)
        return ProductService._add_products_flag(products, favorites_ids)
    
    @staticmethod
    def for_favorites_list(*, user=None) -> list[dict]:
        if not user:
            return []

        favorites_ids = FavoritesClient.get_user_favorites_ids(user)
        qs = FavoritesClient.get_qs_favs_products(
            user, 
            favorites_ids=favorites_ids
        )
        products = ProductService._product_list(qs, ProductService.VALUES_CARDS_LIST)
        return ProductService._add_products_flag(products, favorites_ids)

    @staticmethod
    def for_card_list(*, user=None) -> list[dict]:
        """
        Return products formatted for card listing.
        Adds `is_favorited` if user is provided.
        """
        if not user:
            return []
        
        qs = Product.objects.all()
        favorites_ids = FavoritesClient.get_user_favorites_ids(user)

        products = ProductService._product_list(qs, ProductService.VALUES_CARDS_LIST)
        return ProductService._add_products_flag(products, favorites_ids)
    
    @staticmethod
    def qs_for_card_list(*, filters: dict) -> QuerySet:
        return ProductService._get_qs_products_filters(
            filters=filters, values=ProductService.VALUES_CARDS_LIST
        )
        
    @staticmethod
    def qs_for_dashboard(*, filters: dict) -> QuerySet:
        """ this is only for dashboard admin, especifics values """
        return ProductService._get_qs_products_filters(
            filters=filters, values=ProductService.VALUES_DASHBOARD_PRODUCTS, sorted_by=('name', 'id')
        )

    @staticmethod
    def serializer_list_add_flags(*, products: list[dict], user=None) -> list[dict]:
        # solo buscar en favorites client si hay user...
        favorites_ids = FavoritesClient.get_user_favorites_ids(user) if user else set() 
        return ProductService._add_products_flag(products, favorites_ids)
    
    # ----- private helpers
    
    @staticmethod
    def _get_detail(
        *,
        entity_id: int | None = None,
        entity_slug: str | None = None,
        values: tuple[str, ...] = ("id", "name"),
    ) -> Product:
        """
        Internal helper to retrieve a single product with selected fields.

        This method supports two lookup strategies:
        - ID + slug (preferred, safer for public URLs)
        - ID only (internal/admin usage)

        Args:
            entity_id (int | None): Product ID.
            entity_slug (str | None): Product slug.
            values (tuple[str, ...]): Fields to load using `.only()`.

        Returns:
            Product: Product model instance.

        Raises:
            Product.DoesNotExist: If no matching product is found, or 
                if no valid lookup parameters are provided.
        """
        qs = (
            Product.objects
            .select_related("subcategory__category", "subcategory", "brand")
            .only(*values)
        )

        if entity_id and entity_slug:
            return qs.get(id=entity_id, slug=entity_slug)

        if entity_id:
            return qs.get(id=entity_id)
        
        raise Product.DoesNotExist
    
    @staticmethod
    def _get_qs_products_filters(
        filters: dict, 
        values: tuple = ('id', 'price', 'name'), 
        sorted_by: tuple = ('price', 'id')
    ) -> QuerySet:
        """
        Filters products based on provided dictionary filters.
        
        Args:
            filters (dict): Dictionary with optional keys:
                - 'category' (id or None Category)
                - 'subcategory' (id or None Subcategory)
                - 'brand' (id or None Brand)
                - 'stock' (bool) -> True to -> stock__gt=0
                - 'query' (str)
                - 'top_query' (str)
                - 'available' (bool)
                - 'get_all' (bool): If True, returns all products regardless of 'available'.
            
        Returns:
            QuerySet[Product]: Filtered queryset (may be empty if no matches).
        """
        get_all = filters.get('get_all', False)      # if u want different value
        available = filters.get('available', True)   # if u want different value
        category = valid_id_or_None(filters.get('category'))            # ID || None
        subcategory = valid_id_or_None(filters.get('subcategory'))      # ID || None
        brand = valid_id_or_None(filters.get('brand'))      # ID || None
        query = filters.get('query', '')               
        top_query = filters.get('top_query', '')            # query STR || ''
        stock = filters.get('stock', False)  

        # Si all está activo, no se filtra por disponibilidad
        products = Product.objects.all() if get_all else Product.objects.filter(available=available)
        
        if stock:
            products = products.filter(stock__gt=0)

        if category:
            products = products.filter(subcategory__category_id=category)

        if subcategory:
            products = products.filter(subcategory_id=subcategory)
            
        if brand:
            products = products.filter(brand_id=brand)
        
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

            fts_qs = products.filter(fts_filter).annotate(rank=fts_rank_expr).order_by('-rank')

            # Si FTS encontró resultados suficientes, devolvemos eso
            if fts_qs.exists():
                products = fts_qs
                logger.debug('[PRODUCTS FILTER] solo fts')
            else:
                # 2. Si FTS falló (0 resultados), ejecutamos Trigram (Lento pero tolerante)
                if len(chain) >= 3:
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
                    
                    products = products.filter(trigram_filter).annotate(
                        rank=Coalesce(trigram_rank_expr, 0.0)
                    ).order_by('-rank')
                    
                    logger.debug('[PRODUCTS FILTER] solo trigram')
                    
            # cancela ordenamiento por defecto
            sorted_by = None
            
        """   
        if query or top_query:
            chain = f"{query} {top_query}".strip()
            words = chain.split()
            
            # -----------------------------
            # Step 1: Build FTS components
            # -----------------------------
            fts_query = None
            fts_rank_expr = None
            fts_filter = Q()
            
            for word in words:
                # FTS prefix query
                q = SearchQuery(f"{word}:*", search_type='raw')
                if fts_query is None:
                    fts_query = q
                else:
                    fts_query |= q
                
                # FTS rank expression
                r = SearchRank(F('search_vector'), SearchQuery(f"{word}:*", search_type='raw'))
                if fts_rank_expr is None:
                    fts_rank_expr = r
                else:
                    fts_rank_expr += r
                
                # FTS filter condition
                fts_filter |= Q(search_vector=SearchQuery(f"{word}:*", search_type='raw'))
            
            # -----------------------------
            # Step 2: Build Trigram components
            # -----------------------------
            trigram_rank_expr = None
            trigram_filter = Q()
            
            if len(chain) >= 3:
                for word in words:
                    # Trigram filter
                    trigram_filter |= Q(normalized_name__icontains=word)
                    
                    # Trigram similarity ranking
                    t = TrigramSimilarity('normalized_name', word)
                    if trigram_rank_expr is None:
                        trigram_rank_expr = t
                    else:
                        trigram_rank_expr += t
                
                # -----------------------------
                # Step 3: Combine both systems with weights
                # -----------------------------
                # Usamos un sistema de puntuación combinada
                # FTS tiene mayor peso para coincidencias exactas
                # Trigram ayuda con palabras cortas y coincidencias parciales
                
            # Aplicamos ambos filtros con OR para máxima cobertura
            combined_filter = fts_filter | trigram_filter
            
            # Creamos una puntuación combinada
            # Normalizamos los rangos (asumiendo que FTS rank es entre 0-1 y trigram 0-1)
            # Pesos: 70% FTS, 30% trigram (ajustables según tus necesidades)
            FTS_WEIGHT = 0.7
            TRIGRAM_WEIGHT = 0.3
            
            products = (
                products
                .filter(combined_filter)
                .annotate(
                    fts_rank=Coalesce(fts_rank_expr, 0.0),
                    trigram_rank=Coalesce(trigram_rank_expr, 0.0)
                )
                .annotate(
                    combined_rank=(
                        (F('fts_rank') * FTS_WEIGHT) + 
                        (F('trigram_rank') * TRIGRAM_WEIGHT)
                    )
                )
                .order_by('-combined_rank', '-fts_rank', '-trigram_rank')
            )
            
            # cancela ordenamiento por defecto
            sorted_by = None
            """
        
        return ProductService._product_qs(qs=products, values=values, sorted_by=sorted_by)
    
    
    @staticmethod
    def _product_qs(
        *, 
        qs: QuerySet, 
        values: tuple, 
        sorted_by: tuple = None
    ) -> QuerySet:
        
        qs = (
            qs
            .values(*values)
            .annotate(
                brand_id=F("brand__id"),
                category_id=F("subcategory__category__id"),
                subcategory_id=F("subcategory__id"),
            )
        )
        if sorted_by is None:
            return qs
        
        return qs.order_by(*sorted_by)

    @staticmethod
    def _product_list(qs, values) -> list[dict]:
        """
        Build the base product card list.
        """
        return list(
            qs
            .values(*values)
            .annotate(
                brand_id=F("brand__id"),
                category_id=F("subcategory__category__id"),
                subcategory_id=F("subcategory__id"),
            )
            .order_by('price', 'id')
        )

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
            discount = Decimal(p.get('discount', 0))
            try:
                price = Decimal(p['price'])
                if discount != 0:
                    p['price_discount'] = (
                        price * (Decimal('1') - discount / Decimal('100'))
                    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                else:
                    p['price_discount'] = price
            except (ValueError, TypeError, KeyError):
                p['price_discount'] = p.get('price', 0)

        return products

