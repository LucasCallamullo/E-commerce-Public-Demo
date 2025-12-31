from django.db.models import F
from orders.models import Invoice


class InvoiceService:
    """
    Service layer responsible for handling business logic related to invoices.

    This service provides read-only operations intended to be reused by
    views, APIs, and other services without duplicating ORM logic.
    """

    @staticmethod
    def get_user_invoices(user):
        """
        Retrieve a list of invoices belonging to a specific user.

        The returned data is optimized for read-only usage (e.g. profile pages),
        using `.values()` to avoid instantiating full model objects and
        `annotate()` to expose related payment method information.

        Args:
            user (User): Authenticated Django user whose invoices will be retrieved.

        Returns:
            list[dict]: A list of dictionaries with the following keys:
                - id (int): Invoice ID
                - updated_at (datetime): Last update timestamp
                - fiscal_total (Decimal): Total amount of the invoice
                - payment_method (str): Name of the payment method used
                - order_id (int): Related order ID
                - is_paid (bool): Whether the invoice has been paid

        Notes:
            - Results are ordered by `updated_at` descending.
            - This method does not perform authentication checks; callers
              should ensure the user is valid and authorized.
        """
        qs = (
            Invoice.objects
            .filter(user=user)
            # .annotate(payment_method=F('order__payment__name'))
            # .values('id', 'updated_at', 'fiscal_total', 'payment_method', 'order_id', 'is_paid')
            .values('id', 'updated_at', 'fiscal_total', 'order_id', 'is_paid', payment_method=F('order__payment__name'))
            .order_by('-updated_at')
        )

        return list(qs)
