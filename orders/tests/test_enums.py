# pytest 
from orders.enums import (
    StatusOrderEnum,
    PaymentMethodEnum,
    ShipmentMethodEnum,
)

# -----------------------------
# StatusOrderEnum
# -----------------------------
def test_status_order_enum_values():
    assert StatusOrderEnum.CANCELLED.value == 1
    assert StatusOrderEnum.PENDING.value == 2
    assert StatusOrderEnum.COMPLETED.value == 6
    assert StatusOrderEnum.RETURNED.value == 7


def test_status_order_enum_labels():
    assert StatusOrderEnum.CANCELLED.label == 'Cancelado'
    assert StatusOrderEnum.PAYMENT_CONFIRMED.label == 'Pago Confirmado'
    assert StatusOrderEnum.RETURNED.label == 'Devolución'


def test_status_order_enum_choices_integrity():
    choices = dict(StatusOrderEnum.choices)

    assert choices[1] == 'Cancelado'
    assert choices[2] == 'Pendiente'
    assert choices[6] == 'Completado'


# -----------------------------
# PaymentMethodEnum
# -----------------------------
def test_payment_method_enum_values():
    assert PaymentMethodEnum.CASH.value == 1
    assert PaymentMethodEnum.TRANSFER.value == 2
    assert PaymentMethodEnum.MERCADO_PAGO.value == 3
    assert PaymentMethodEnum.CRYPTO.value == 4


def test_payment_method_enum_labels():
    assert PaymentMethodEnum.CASH.label == 'Efectivo'
    assert PaymentMethodEnum.MERCADO_PAGO.label == 'Mercado Pago'


# -----------------------------
# ShipmentMethodEnum
# -----------------------------
def test_shipment_method_enum_values():
    assert ShipmentMethodEnum.PICKUP.value == 1
    assert ShipmentMethodEnum.LOCAL.value == 2
    assert ShipmentMethodEnum.OUTSIDE.value == 3
    assert ShipmentMethodEnum.POST_OFFICE.value == 4


def test_shipment_method_enum_labels():
    assert ShipmentMethodEnum.PICKUP.label == 'Retiro en Local'
    assert ShipmentMethodEnum.POST_OFFICE.label == 'Puntos de Retiro Correo'
