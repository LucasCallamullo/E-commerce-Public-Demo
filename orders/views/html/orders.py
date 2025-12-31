

from django.shortcuts import render
# Create your views here.

from orders.services.orders_draft import OrderDraftService
from orders.services.shipment_methods import ShipmentMethodService
from orders.services.payment_methods import PaymentMethodService

from orders.utils import get_order_detail_context

def order_detail(request, order_id):
    user = request.user
    if not user.is_authenticated:    # Stupids checks for problematic users
        return render(request, "payments/fail_payments.html", {"error": "Debes iniciar sesión para pagar."})
    
    context = get_order_detail_context(order_id, user)
    if not context:
        render(request, "payments/fail_payments.html", {"error": "Order Not Found."})
    
    return render(request, "orders/order_detail.html", context)




def resume_order(request):
    """
    Checkout entrypoint.

    - Shows checkout form (validated later using serializers)
    - Loads available shipment and payment methods
    - Creates or reuses an OrderDraft (cart snapshot) for the user

    Flow:
        1) If the user is not authenticated → redirect to registration/login.
        2) Take a snapshot of the cart (JSON).
        3) Create or reuse a single OPEN draft for this user.
        4) Always keep the draft in sync with the latest cart state.
    """

    from users.models import Provincia
    
    def _redirect_to_login():
        context = {
            "flag_to_login": True,
            "provinces": Provincia.choices,
        }
        return render(request, "users/register_user.html", context)

    # 1. Require authentication
    if not request.user.is_authenticated:
        return _redirect_to_login()

    # 2. OrderDraft service
    draft = OrderDraftService.get_or_create_draft(request=request)

    # Stupid check - Defensive fallback (should almost never happen)
    if draft is None:
        return _redirect_to_login()

    # 3. Render checkout
    return render(
        request,
        "orders/resume_order.html",
        {
            "shipment_methods": ShipmentMethodService.for_checkout(),
            "payment_methods": PaymentMethodService.for_checkout(),
            "provinces": Provincia.choices,
        },
    )
