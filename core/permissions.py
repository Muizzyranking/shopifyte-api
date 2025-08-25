from typing import Any, Callable
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
    request: HttpRequest, permissions: list[BasePermission], view_func: Any = None
):
    if not permissions:
        return True

    for permission in permissions:
        if not permission.has_permission(request, view_func):
            permission.permission_denied()

    return True


def execute_view(
    view_func: Callable, request: HttpRequest, permissions: list[BasePermission], *args, **kwargs
):
    check_permissions(request, permissions, view_func)
    return view_func(request, *args, **kwargs)
