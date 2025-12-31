# orders/services/shipment_methods.py
from typing import Any, Iterable
from orders.models import ShipmentMethod


class ShipmentMethodService:
    """
    Service responsible for retrieving shipment method data.
    """

    @staticmethod
    def _get_all(
        *,
        values: Iterable[str],
        only_active: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Internal helper to retrieve shipment methods with custom fields.
        """
        qs = ShipmentMethod.objects.all()

        if only_active:
            qs = qs.filter(is_active=True)

        return list(qs.values(*values).order_by('id'))

    # ---------- Public API ----------

    @staticmethod
    def for_admin() -> list[dict[str, Any]]:
        """
        Shipment methods including administrative fields.
        """
        return ShipmentMethodService._get_all(
            values=('id', 'name', 'price', 'is_active', 'description')
        )

    @staticmethod
    def for_checkout() -> list[dict[str, Any]]:
        """
        Shipment methods available for checkout.
        """
        return ShipmentMethodService._get_all(
            values=('id', 'name', 'price', 'description'),
            only_active=True,
        )

    @staticmethod
    def for_filters() -> list[dict[str, Any]]:
        """
        Shipment methods optimized for filters or selects.
        """
        return ShipmentMethodService._get_all(
            values=('id', 'name'),
            only_active=True,
        )
