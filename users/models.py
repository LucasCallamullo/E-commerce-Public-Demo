# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager


class Provincia(models.TextChoices):
    BUENOS_AIRES = 'buenos_aires', 'Buenos Aires'
    CATAMARCA = 'catamarca', 'Catamarca'
    CHACO = 'chaco', 'Chaco'
    CHUBUT = 'chubut', 'Chubut'
    CABA = 'caba', 'Ciudad Autónoma de Buenos Aires'
    CORDOBA = 'cordoba', 'Córdoba'
    CORRIENTES = 'corrientes', 'Corrientes'
    ENTRE_RIOS = 'entre_rios', 'Entre Ríos'
    FORMOSA = 'formosa', 'Formosa'
    JUJUY = 'jujuy', 'Jujuy'
    LA_PAMPA = 'la_pampa', 'La Pampa'
    LA_RIOJA = 'la_rioja', 'La Rioja'
    MENDOZA = 'mendoza', 'Mendoza'
    MISIONES = 'misiones', 'Misiones'
    NEUQUEN = 'neuquen', 'Neuquén'
    RIO_NEGRO = 'rio_negro', 'Río Negro'
    SALTA = 'salta', 'Salta'
    SAN_JUAN = 'san_juan', 'San Juan'
    SAN_LUIS = 'san_luis', 'San Luis'
    SANTA_CRUZ = 'santa_cruz', 'Santa Cruz'
    SANTA_FE = 'santa_fe', 'Santa Fe'
    SANTIAGO_DEL_ESTERO = 'santiago_del_estero', 'Santiago del Estero'
    TIERRA_DEL_FUEGO = 'tierra_del_fuego', 'Tierra del Fuego'
    TUCUMAN = 'tucuman', 'Tucumán'


# Custom User Manager responsible for creating users and superusers
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        # Raise an error if no email is provided
        if not email:
            raise ValueError('The Email field must be set')
        
        # Normalize the email to ensure correct format
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        # Set the encrypted password
        user.set_password(password)
        # Save the user to the database
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        # Ensure that superusers have specific permissions
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # Call the regular user creation for the superuser
        return self.create_user(email, password, **extra_fields)


# Modelo de usuario personalizado que reemplaza al modelo por defecto de Django
class CustomUser(AbstractUser):
    # Remove the 'username' field from the default model
    username = None 

    email = models.EmailField(unique=True)  # The email field must be unique for each user
    cellphone = models.CharField(max_length=20, blank=True, null=True)  # Phone number (optional)
    
    # User's province (optional)
    province = models.CharField(
    max_length=30,
        choices=Provincia.choices,
        default=Provincia.CORDOBA,
        blank=True,
        null=True,
    )
    address = models.CharField(max_length=200, blank=True, null=True)  # User's address (optional)
    dni = models.CharField(max_length=20, blank=True, null=True)  # User's address (optional)

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('seller', 'Vendedor'),
        ('buyer', 'Comprador'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')

    """ 
    Other fields:
    first_name: User's first name.
    last_name: User's last name.
    is_active: Boolean indicating if the user is active.
    is_staff: Boolean indicating if the user has admin privileges.
    is_superuser: Boolean indicating if the user is a superuser.
    last_login: Date and time of the user's last login.
    date_joined: Date and time when the user registered.
    groups: Groups the user belongs to.
    user_permissions: Specific permissions assigned to the user.
    """

    # Use email instead of 'username' for authentication
    USERNAME_FIELD = "email"

    # No additional fields are required to create a superuser (by default only email and password are needed)
    REQUIRED_FIELDS = []  # If you add extra fields, list them here

    # Assign the CustomUserManager to handle user creation
    objects = CustomUserManager()

    # Method to represent the user as a string (using email)
    def __str__(self):
        return self.email  # Returns the email address as the user's string representation
