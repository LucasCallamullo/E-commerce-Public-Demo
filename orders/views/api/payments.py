from rest_framework.views import APIView
from rest_framework.response import Response
# core app
from core.permissions import IsAdminOrSuperUser
from core.views.get_object_mixin import GetObjectMixin

from orders.models import PaymentMethod
from orders.serializers.methods import PaymentSerializer


class PaymentAPI(APIView, GetObjectMixin):
    permission_classes = [IsAdminOrSuperUser]
    
    def patch(self, request, pk: int | str) -> Response:
        """
        Partially updates a specific payment method.
        
        1. Retrieves the model instance using GetObjectMixin.
        2. Validates incoming JSON data via PaymentSerializer.
        3. Persists changes using optimized SQL updates.
        """
        payment = self._get_payment_method(payment_id=pk)
        
        # Initialize serializer with partial=True for PATCH operations
        serializer = PaymentSerializer(payment, data=request.data, partial=True)

        # Delegate validation and error raising to the serializer
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return self.success_response(data=serializer.data, key='payment_method')

    def get(self, request, pk: int | str = None) -> Response:
        """
        Retrieves payment methods.
        
        If 'pk' is provided: Returns a single object as a dictionary.
        If 'pk' is None: Returns a list of all payment methods.
        """
        if pk:
            # Use Mixin to retrieve a specific record as a dict (DB optimized)
            payment = self.get_values_or_error(PaymentMethod, pk)
            return self.success_response(data=payment, key="payment_method")
        
        # Retrieve all records as a list of dictionaries to bypass model instantiation overhead
        payments = list(PaymentMethod.objects.all().values())
        return self.success_response(
            data=payments,
            key="payment_methods",
            count=len(payments)
        )
        
    def _get_payment_method(self, payment_id: int | str) -> PaymentMethod:
        """
        Fetch a PaymentMethod instance or raise 404/400.
        """
        return self.get_instance_or_error(
            model_class=PaymentMethod,
            obj_id=payment_id
        )
    