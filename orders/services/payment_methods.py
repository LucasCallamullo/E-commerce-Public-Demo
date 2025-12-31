# orders/services/payment_methods.py
from typing import Any, Iterable
from orders.models import PaymentMethod


class PaymentMethodService:
    """
    Service responsible for retrieving payment method data.
    """

    @staticmethod
    def _get_all(
        *,
        values: Iterable[str],
        only_active: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Internal helper to retrieve payment methods with custom fields.

        Args:
            values (Iterable[str]): Fields to include in the result.
            only_active (bool): Whether to return only active methods.

        Returns:
            list[dict[str, Any]]: List of payment method dictionaries.
        """
        qs = PaymentMethod.objects.all()

        if only_active:
            qs = qs.filter(is_active=True)

        return list(qs.values(*values).order_by('id'))

    # ---------- Public API ----------

    @staticmethod
    def for_admin() -> list[dict[str, Any]]:
        """
        Payment methods including administrative fields.
        """
        return PaymentMethodService._get_all(
            values=('id', 'name', 'time', 'is_active', 'description')
        )

    @staticmethod
    def for_checkout() -> list[dict[str, Any]]:
        """
        Payment methods available for checkout.
        """
        return PaymentMethodService._get_all(
            values=('id', 'name', 'time', 'description'),
            only_active=True,
        )

    @staticmethod
    def for_filters() -> list[dict[str, Any]]:
        """
        Payment methods optimized for filters or selects.
        """
        return PaymentMethodService._get_all(
            values=('id', 'name'),
            only_active=True,
        )
