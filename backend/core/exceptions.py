from django.http import Http404
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
)
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler.

    Wraps all error responses in a consistent envelope:
    {
        "error": true,
        "code":  "permission_denied",
        "message": "You do not have permission to perform this action.",
        "detail": { ... }   ← original DRF detail (optional)
    }
    """
    # Let DRF build the base response first
    response = exception_handler(exc, context)

    if response is not None:
        error_code = "error"
        message    = str(exc)

        if isinstance(exc, NotAuthenticated):
            error_code = "not_authenticated"
            message    = "Authentication credentials were not provided."
        elif isinstance(exc, AuthenticationFailed):
            error_code = "authentication_failed"
            message    = "Invalid authentication credentials."
        elif isinstance(exc, PermissionDenied):
            error_code = "permission_denied"
            message    = "You do not have permission to perform this action."
        elif isinstance(exc, ValidationError):
            error_code = "validation_error"
            message    = "Invalid data provided."
        elif isinstance(exc, Http404):
            error_code = "not_found"
            message    = "The requested resource was not found."

        response.data = {
            "error":   True,
            "code":    error_code,
            "message": message,
            "detail":  response.data,
        }

    return response


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class HierarchyError(Exception):
    """Raised when a hierarchy validation fails (e.g., cycle detected)."""
    pass


class AccessDeniedError(PermissionDenied):
    """Raised when a user tries to access an OrgUnit they are not assigned to."""
    default_detail = "You do not have access to this organizational unit."
    default_code   = "org_access_denied"


class InvalidHierarchyLevelError(ValidationError):
    """Raised when an OrgUnit is assigned an incompatible hierarchy level."""
    default_detail = "The hierarchy level is not valid for this operation."
    default_code   = "invalid_hierarchy_level"
