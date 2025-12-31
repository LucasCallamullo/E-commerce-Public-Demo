# orders/enums.py
from django.db.models import IntegerChoices


class StatusOrderEnum(IntegerChoices):
    """
    Represents the fixed status codes for an Order.

    This enum is tightly coupled to the `StatusOrder` master table.
    The integer values defined here MUST match the primary keys (IDs)
    stored in the database.

    These values are considered part of the business contract and
    should not be changed once the system is in production.

    Labels are intended for display purposes and may differ from
    database descriptions.
    """
    CANCELLED = 1, 'Cancelado'
    PENDING = 2, 'Pendiente'
    PAYMENT_PENDING = 3, 'Pago a Confirmar'
    PAYMENT_CONFIRMED = 4, 'Pago Confirmado'
    SHIPPED = 5, 'Enviado'
    COMPLETED = 6, 'Completado'
    RETURNED = 7, 'Devolución'


class PaymentMethodEnum(IntegerChoices):
    """
    Represents the supported payment methods.

    This enum mirrors the IDs of the `PaymentMethod` master table.
    Each value corresponds to a concrete payment flow with
    potentially different business rules and processing logic.

    IDs are fixed and should remain stable to avoid breaking
    historical data and integrations.
    """
    CASH = 1, 'Efectivo'
    TRANSFER = 2, 'Transferencia directa'
    MERCADO_PAGO = 3, 'Mercado Pago'
    CRYPTO = 4, 'Criptomoneda'


class ShipmentMethodEnum(IntegerChoices):
    """
    Represents the available shipment and pickup methods.

    This enum maps directly to the `ShipmentMethod` master table.
    Each value may imply different validation rules, pricing
    strategies, or required customer data.

    The integer values are part of the domain contract and must
    match the database identifiers.
    """
    PICKUP = 1, 'Retiro en Local'
    LOCAL = 2, 'Dentro de Circunvalación'
    OUTSIDE = 3, 'Fuera de Circunvalación'
    POST_OFFICE = 4, 'Puntos de Retiro Correo'
