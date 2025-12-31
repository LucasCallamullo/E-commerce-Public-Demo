

from drf_spectacular.utils import OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes


AUTH_401_RESPONSE = OpenApiResponse(
    response=OpenApiTypes.OBJECT,
    description="Authentication required",
    examples=[
        OpenApiExample(
            name="Not authenticated",
            value={
                "detail": "Authentication credentials were not provided."
            }
        )
    ]
)


PERMISSION_403_RESPONSE = OpenApiResponse(
    response=OpenApiTypes.OBJECT,
    description="Insufficient permissions",
    examples=[
        OpenApiExample(
            name="Permission denied",
            value={
                "detail": "You do not have permission to perform this action."
            }
        )
    ]
)



def invalid_id_response(resource_name: str):
    """
    Generate an OpenAPI example for an invalid resource ID.

    Args:
        resource_name (str): The name of the resource (e.g., "User", "Product").

    Returns:
        OpenApiExample: An OpenAPI example object representing an invalid ID error.
    """
    return OpenApiExample(
        name=f"Invalid {resource_name} ID",
        summary=f"{resource_name} ID is invalid",
        value={
            "success": False,
            "detail": f"{resource_name} ID Incorrect."
        }
    )


def not_found_response(resource_name: str):
    """
    Generate an OpenAPI response for a resource that was not found.

    Args:
        resource_name (str): The name of the resource (e.g., "User", "Product").

    Returns:
        OpenApiResponse: An OpenAPI response object representing a "not found" error.
    """
    return OpenApiResponse(
        response=OpenApiTypes.OBJECT,
        description=f"{resource_name} not found",
        examples=[
            OpenApiExample(
                name=f"{resource_name} not found",
                summary=f"{resource_name} not found",
                value={
                    "success": False,
                    "detail": f"{resource_name} not found."
                }
            )
        ]
    )
