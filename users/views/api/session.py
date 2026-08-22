

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth import login, logout
from django.urls import reverse

from users.serializers.session import RegisterLoginSerializer, WidgetLoginSerializer

# acoplamiento con Carrito de la app 'cart'
from cart.carrito import Carrito


class RegisterUserView(APIView):
    # rate limit on this view, 5/min
    throttle_scope = 'auth_heavy'
    
    def post(self, request):    
        # When you pass `data=params`, the serializer calls the `validate` methods
        serializer = RegisterLoginSerializer(data=request.data)  
        
        # devuelve 400 si da error
        serializer.is_valid(raise_exception=True)
          
        # Calling `.save()` triggers the `create()` or `update()` method in the serializer
        user = serializer.save()  # Executes `create()` and returns a `CustomUser` instance
        login(request, user)      # Logs the user into the Django session
        
        # To return the `CustomUser` object as JSON, pass it to the serializer without `data=`.
        # This tells the serializer to serialize the object instead of validating it.
        
        # obtiene Url desde la data o envía directo al perfil
        next_url = request.data.get("next")
        redirect_url = next_url or reverse("profile_user")

        # Prepare the response with data     
        return Response({
            "user": RegisterLoginSerializer(user).data,
            "detail": "Registration successful!",
            "redirect_url": redirect_url
        }, status=status.HTTP_201_CREATED)
    

class LoginView(APIView):
    # rate limit on this view, 5/min
    throttle_scope = 'auth_heavy'
    
    """
    View that handles the login of a registered user.

    Receives the form data from "widget_login.html" and validates it using the WidgetLoginSerializer.
    If the data is valid, the user is authenticated and logged in to the Django session.
    """
    def post(self, request):
        serializer = WidgetLoginSerializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)
        
        # Get data from the serializer's response
        user = serializer.validated_data["user"]
        
        """
        # authenticate() es opcional aquí porque YA validamos password
        # Pero lo dejamos por si hay backends custom o lógica adicional
        user = authenticate(
            request,  # ← Pasar request es buena práctica
            email=user.email, 
            password=request.data.get("password")  # O usar otra forma
        ) """ 
        
        # login() maneja la sesión Django
        login(request, user)
        
        # Respuesta enriquecida para el frontend
        return Response({
            "detail": "Login successful!",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "role": user.role if hasattr(user, 'profile') else 'buyer'
            },
            # devuelve la URL con el name 'profile_user' como STR para usar
            "redirect_url": reverse('profile_user')
        }, status=status.HTTP_200_OK)
        

class CloseView(APIView):
    """
        View that handles user logout by terminating the current Django session.
    """
    permission_classes = [IsAuthenticated]  # Only authenticated users can log out

    def post(self, request):

        # 1. Use the Cart service to get the cart stored in the session
        cart = Carrito(request)
        cart_data = cart.carrito    # retrieves cart or {}

        # Log the user out
        # this destroys the current session
        logout(request)

        # Create a new cart instance using the new (anonymous) session
        if cart_data:
            cart2 = Carrito(request)
            cart2.sync_cart_on_logout(cart_data)

        return Response({
            "detail": "Session closed successfully.",
            "redirect_url": reverse('Home')
        }, status=status.HTTP_200_OK)
