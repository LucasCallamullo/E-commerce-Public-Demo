import logging
logger = logging.getLogger(__name__)

from orders.models import OrderDraft

# service externo
from cart.carrito import Carrito


class OrderDraftService:
    
    @staticmethod
    def get_or_create_draft(*, request) -> OrderDraft | None:
        """
        Returns the user's OPEN OrderDraft, creating one if it does not exist.

        Rules:
        - Only ONE draft with status OPEN per user.
        - Always syncs the cart snapshot with the current session cart.

        Return:
            - None: if the user is not authenticated (prevent check).
            - OrderDraft: curso normal
            
        Example:
            - draft.cart --> save this:
                {
                    "items": [
                        {
                            "id": 41,
                            "name": "Peluche Espeon",
                            "slug": "peluche-espeon",
                            "price": 5000.0,
                            "image": "https://i.ibb.co/5hcz0zs0/246d972c1efc4.webp",
                            "quantity": 1,
                            "stock": 10,
                            "discount": 10
                        },
                    ],
                    "total_price": 10000.0,
                    "total_price_discount": 9000.0,
                    "total_quantity": 4
                }
        """
        if not request.user.is_authenticated:
            logger.warning(
                "OrderDraftService.get_or_create_draft() called without authenticated user — ignoring"
            )
            return None

        # recupera carrito en session
        cart = Carrito(request=request)
        cart_json = cart.get_cart_serializer()

        # logger.debug("[CART JSON] -> %s", cart_json)

        # ------------------------------------------------------------------
        # OrderDraft behavior
        #
        # We maintain ONLY ONE draft with status OPEN per user.
        #
        # Scenario 1 — user already started checkout earlier:
        #     - An existing OPEN draft is found
        #     - We DO NOT create a new one
        #     - We simply update the cart snapshot
        #
        # Scenario 2 — user changes the cart in another tab/device:
        #     - User returns to checkout
        #     - We reuse the same OPEN draft
        #     - We overwrite the cart snapshot with the latest data
        #
        # Result:
        #     ✔ no duplicate drafts
        #     ✔ checkout always reflects the real cart
        # ------------------------------------------------------------------
        draft, created = OrderDraft.objects.get_or_create(
            user=request.user,
            status="OPEN",
            defaults={"cart": cart_json},
        )

        if not created:
            draft.cart = cart_json
            draft.save()

        # logger.debug("[DRAFT JSON] -> %s", draft.cart)
        
        return draft
