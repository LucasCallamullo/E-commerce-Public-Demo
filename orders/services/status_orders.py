# orders/services/status_orders.py
from typing import Any, Iterable
from orders.models import StatusOrder


class StatusOrderService:
    """
    Service responsible for retrieving order status data.
    """

    @staticmethod
    def get_all_statuses(values: Iterable[str]) -> list[dict[str, Any]]:
        """
        Retrieve all order statuses with the given fields.

        Args:
            values (Iterable[str]): Fields to include in the result.

        Returns:
            list[dict[str, Any]]: List of status dictionaries.
        """
        return list(
            StatusOrder.objects
            .values(*values)
            .order_by('id')
        )

    @staticmethod
    def for_filters() -> list[dict[str, Any]]:
        """
        Status list optimized for filter dropdowns.
        """
        return StatusOrderService.get_all_statuses(('id', 'name'))

    @staticmethod
    def for_admin() -> list[dict[str, Any]]:
        """
        Status list including administrative fields.
        """
        return StatusOrderService.get_all_statuses(('id', 'name', 'description'))
