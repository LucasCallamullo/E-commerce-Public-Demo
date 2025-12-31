

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from products.services.products import ProductService
from django.db.models import QuerySet

class PaginationService:
    

    @staticmethod
    def get_paginated_products(*, qs: QuerySet, page: int, page_size: int, user):
        """
        Paginates a Product queryset and serializes the resulting page
        with user-specific flags.

        This method acts as an orchestration layer that combines:
        - QuerySet pagination using Django's Paginator
        - Product serialization
        - User-dependent flags enrichment

        Parameters:
            qs (QuerySet):
                Base Product queryset to be paginated.

            page (int):
                Current page number (1-based). May be a string or None;
                invalid or missing values are handled safely by the paginator.

            page_size (int):
                Maximum number of products per page.

            user (User):
                Authenticated user used to compute user-specific flags
                (e.g. favorites, permissions, availability).

        Returns:
            tuple:
                - products (list[dict]):
                    List of serialized products for the current page,
                    enriched with user-specific flags.
                - pagination (dict):
                    Pagination metadata with the following structure:
                    {
                        "page": int,              # Current page number
                        "page_size": int,         # Maximum results per page
                        "total_pages": int,       # Total number of pages
                        "results_on_page": int,   # Results returned in this page
                        "total_results": int      # Total number of available results
                    }
        """
        products_page, pagination = PaginationService._get_paginator(
            products=qs, 
            page_num=page, 
            quantity=page_size
        )
        
        products = ProductService.serializer_list_add_flags(
            products=products_page, 
            user=user
        )
        return products, pagination
    
    @staticmethod
    def _get_paginator(*, products: QuerySet, page_num: int = 1, quantity: int = 100) -> tuple:
        """
        Paginates a Django QuerySet and returns the items for the current page
        along with pagination metadata.

        Args:
            products (QuerySet): Django QuerySet to be paginated.
            page_num (int): Current page number (defaults to 1).
            quantity (int): Number of items per page (defaults to 48).

        Returns:
            tuple: A tuple containing:
                - products_page (QuerySet): A sliced QuerySet containing items for the current page.
                If no items exist, returns the full original QuerySet or an empty list.
                - pagination (dict): A dictionary with pagination metadata:
                    - 'page' (int): Current page number, or 0 if no valid page exists.
                    - 'total_pages' (int): Total number of pages available.
        """
        paginator = Paginator(products, quantity)
        
        if page_num is None:
            page_num = 1

        try:
            # 3. Obtener la página actual
            page_obj = paginator.page(page_num)
        except PageNotAnInteger:
            # Si 'page' no es un entero, mostrar la primera página
            page_obj = paginator.page(1)
        except EmptyPage:
            # Si la página está fuera de rango (ej: 9999), mostrar la última página
            # page_obj = paginator.page(paginator.num_pages)
            if paginator.num_pages == 0:
                # No hay ningún resultado, devolver None o lista vacía segura
                page_obj = None
            else:
                # Página fuera de rango, mostrar la primera
                page_obj = paginator.page(1)
        
        # en este punto ya es lista en memoria
        # products_page = page_obj.object_list if page_obj else products
        products_page = list(page_obj.object_list) if page_obj else []
        
        pagination = {
            'page': page_obj.number if page_obj else 0,
            'page_size': paginator.per_page,
            'total_pages': page_obj.paginator.num_pages if page_obj else 0,
            'results_on_page': len(products_page),
            'total_results': paginator.count
        }
        return products_page, pagination