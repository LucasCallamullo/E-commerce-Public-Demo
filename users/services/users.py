# users/services/user_service.py
from typing import Any
from django.db.models import Q

from users.models import CustomUser

class UserService:
    """
    Service layer for user-related read operations.

    This class contains read-only queries related to users,
    organized by use case (sales, admin, utilities).
    """
    
    # Common fields for sales-related user listings
    VALUES_FOR_SALE = (
        "id",
        "role",
        "first_name",
        "last_name",
        "email",
        "dni",
        "cellphone",
    )

    @staticmethod
    def get_users_for_sale(*, search: str, filter_by: str) -> list[dict]:
        """
        Retrieve users filtered by a search term and filter type,
        optimized for sales/autocomplete use cases.

        Supported filters:
        - dni
        - name (matches first_name OR last_name, word by word)
        - email
        - cellphone

        Args:
            search (str): Text to search.
            filter_by (str): Field to filter by.

        Returns:
            list[dict]: List of users matching the criteria.
        """
        if filter_by not in ("dni", "name", "email", "cellphone"):
            return []

        values = UserService.VALUES_FOR_SALE

        if filter_by == "name":
            # Split the search string into individual words.
            # Example: "?search=juan perez" → ["juan", "perez"]
            words = search.split()

            # Build a dynamic query where EACH word must match
            # either the first_name OR the last_name field.
            #
            # This results in a query equivalent to:
            # (first_name ILIKE '%juan%' OR last_name ILIKE '%juan%')
            # AND
            # (first_name ILIKE '%perez%' OR last_name ILIKE '%perez%')
            name_query = Q()
            for word in words:
                name_query &= (
                    Q(first_name__icontains=word) |
                    Q(last_name__icontains=word)
                )

            qs = CustomUser.objects.filter(name_query).values(*values)
            return list(qs)

        # Mapping of allowed filters to their corresponding query expressions
        filter_map = {
            "dni": Q(dni__icontains=search),
            "email": Q(email__icontains=search),
            "cellphone": Q(cellphone__icontains=search),
        }

        # Apply the selected filter
        qs = CustomUser.objects.filter(filter_map[filter_by]).values(*values)
        return list(qs)

    @staticmethod
    def get_all_limit_for_sale(limit: int = 30) -> list[dict]:
        """
        Retrieve a limited list of users for sales views.

        Args:
            limit (int): Maximum number of users to return.

        Returns:
            list[dict]: List of users.
        """
        return UserService._get_all_limit(
            limit=limit,
            values=UserService.VALUES_FOR_SALE
        )

    @staticmethod
    def _get_all_limit(*, limit: int = 30, values: tuple[str, ...]) -> list[dict]:
        """
        Internal helper to retrieve a limited list of users
        with custom fields.

        Args:
            limit (int): Maximum number of users.
            values (tuple[str]): Fields to include.

        Returns:
            list[dict]: List of user dictionaries.
        """
        return list(
            CustomUser.objects
            .values(*values)
            .order_by("id")[:limit]
        )

    @staticmethod
    def get_admin_users(
        *,
        search: str | None = None,
        role: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve users for admin listings with optional filters.

        Filters:
        - search: partial email match
        - role: exact role match

        Args:
            search (str | None): Email search term.
            role (str | None): User role filter.

        Returns:
            list[dict[str, Any]]: List of user dictionaries.
        """
        qs = CustomUser.objects.all()

        if search:
            qs = qs.filter(email__icontains=search)

        if role:
            qs = qs.filter(role=role)

        return list(
            qs.values(
                "id",
                "first_name",
                "last_name",
                "email",
                "role",
            )
        )

    @staticmethod
    def get_role_choices() -> dict[str, str]:
        """
        Retrieve available user role choices.

        Returns:
            dict[str, str]: Role value → label mapping.
        """
        return dict(CustomUser.ROLE_CHOICES)

    @staticmethod
    def update_user_role(*, user_id: int, role: str) -> dict:
        """
        Update a user's role.

        Args:
            user_id (int): User ID.
            role (str): New role.

        Returns:
            dict: Updated user data.

        Raises:
            ValueError: If role is invalid.
            CustomUser.DoesNotExist: If user does not exist.
        """
        role = role.lower().strip()
        roles = {"admin", "seller", "buyer"}

        if role not in roles:
            raise ValueError()

        user = CustomUser.objects.get(id=user_id)    # tira raise si no encuentra
        user.role = role
        user.save(update_fields=["role"])

        return {
            "id": user.id,
            "role": user.role,
        }