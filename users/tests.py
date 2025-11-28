

# Create your tests here.
from django.test import TestCase
from django.contrib.auth import get_user_model


class CustomUserManagerTests(TestCase):
    def setUp(self):
        """
        Configura un entorno de prueba inicial donde se pueden crear usuarios.
        """
        self.email = "testuser@example.com"
        self.password = "TestPassword123"
        self.extra_fields = {
            "cellphone": "1234567890",
            "province": "Some Province",
            "address": "Some Address"
        }

    def test_create_user_with_email_and_password(self):
        """
        Verifica que se pueda crear un usuario con el email y la contraseña.
        """
        user = get_user_model().objects.create_user(
            email=self.email,
            password=self.password,
            **self.extra_fields
        )

        self.assertEqual(user.email, self.email)
        self.assertTrue(user.check_password(self.password))
        self.assertTrue(user.is_active)  # El usuario debe estar activo por defecto
        self.assertFalse(user.is_staff)  # El usuario no es staff por defecto
        self.assertFalse(user.is_superuser)  # El usuario no es superusuario por defecto

    def test_create_superuser(self):
        """
        Verifica que se pueda crear un superusuario con los campos adecuados.
        """
        superuser = get_user_model().objects.create_superuser(
            email="superuser@example.com",
            password="SuperPassword123",
            **self.extra_fields
        )

        self.assertEqual(superuser.email, "superuser@example.com")
        self.assertTrue(superuser.check_password("SuperPassword123"))
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_create_superuser_with_invalid_is_staff(self):
        """
        Verifica que se genere un error si se intenta crear un superusuario sin los permisos adecuados.
        """
        with self.assertRaises(ValueError):
            get_user_model().objects.create_superuser(
                email="invalidsuperuser@example.com",
                password="SuperPassword123",
                is_staff=False,  # Invalid staff permission
                **self.extra_fields
            )

    def test_create_superuser_with_invalid_is_superuser(self):
        """
        Verifica que se genere un error si se intenta crear un superusuario sin el permiso is_superuser.
        """
        with self.assertRaises(ValueError):
            get_user_model().objects.create_superuser(
                email="invalidsuperuser@example.com",
                password="SuperPassword123",
                is_superuser=False,  # Invalid superuser permission
                **self.extra_fields
            )

    def test_create_user_without_email(self):
        """
        Verifica que se genere un error si se intenta crear un usuario sin un email.
        """
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email=None,  # Email no proporcionado
                password=self.password,
                **self.extra_fields
            )

    def test_user_string_representation(self):
        """
        Verifica que la representación en cadena del usuario sea correcta (usando el email).
        """
        user = get_user_model().objects.create_user(
            email=self.email,
            password=self.password,
            **self.extra_fields
        )
        self.assertEqual(str(user), self.email)
