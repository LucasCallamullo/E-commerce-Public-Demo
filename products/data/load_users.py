

from django.contrib.auth.hashers import make_password
from users.models import CustomUser


def load_users_init():
    # Crear superusuario
    user, created = CustomUser.objects.get_or_create(
        # id=1,  # Forzar ID=1
        email="lucascallamullo98@gmail.com",
        defaults={
            "password": make_password("Cerezita!1998"),
            "first_name": "Admin",
            "last_name": "SuperAdmin",
            "is_active": True,
            "is_staff": True,
            "is_superuser": True,
            "role": 'admin',
        }
    )
    
    if created:
        print(f'El Super usuario {user.email} Se creo exitosamente')

    # Crear usuarios de ejemplo
    users = [
        {"email": "lucascallamullo@hotmail.com", "first_name": "Comprador", "last_name": "Anonimo"},
        {"email": "user1@gmail.com", "first_name": "Lucas", "last_name": "Martinez"},
        {"email": "user2@gmail.com", "first_name": "Ariana", "last_name": "Romero"},
        {"email": "user3@gmail.com", "first_name": "Sofía", "last_name": "Sarasola"},
    ]
    
    for user_data in users:
        
        user, created = CustomUser.objects.get_or_create(
            email=user_data["email"],
            defaults={
                "password": make_password("1234"),
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "is_active": True,
            }
        )
        
        if created:
            print(f'El usuario {user.email} Se creo exitosamente')
        else:
            print(f"El usuario {user.email} ya existia")

    
if __name__ == "__main__":
    load_users_init()
