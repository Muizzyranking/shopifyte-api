from typing import Any, Union
from django.http import HttpRequest


class PermissionDenied(Exception):
    """Exception raised when a permission is denied."""

    def __init__(self, message="Permission Denied", status_code=403):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class BasePermission:
    message = "You do not have permission to perform this action."
    status_code = 403
    exception = PermissionDenied

    def has_permission(self, request: HttpRequest, view_func: Any = None) -> bool:
        raise NotImplementedError("Permission classes must implement has_permission method.")

    def permission_denied(self, message: str = None, status_code: int = None):
        message = message or self.message
        status_code = status_code or self.status_code
        raise self.exception(message=message, status_code=status_code)


def check_permissions(
    request: HttpRequest,
    permissions: Union[list[BasePermission], BasePermission],
    view_func: Any = None,
):
    """
    Checks if the request has the required permissions.
    """
    if not permissions:
        return True

    if not isinstance(permissions, list):
        permissions = [permissions]

    for permission in permissions:
        permission_instance = None
        if isinstance(permission, type) and issubclass(permission, BasePermission):
            permission_instance = permission()
        elif isinstance(permission, BasePermission):
            permission_instance = permission
        else:
            continue

        if not permission_instance.has_permission(request, view_func):
            permission_instance.permission_denied()

    return True
