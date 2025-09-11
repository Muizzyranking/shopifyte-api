from enum import Enum
from functools import wraps
import types
from typing import Any, List, Union

from ninja import Router
from ninja.constants import NOT_SET

from core.permissions import BasePermission, check_permissions
from core.schemas import (
    BadRequestResponseSchema,
    ErrorResponseSchema,
    ForbiddenResponseSchema,
    NotFoundResponseSchema,
    UnauthorizedResponseSchema,
    ValidationErrorResponseSchema,
)


class Methods(str, Enum):
    POST = "POST"
    GET = "GET"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class CustomRouter(Router):
    """
    Modified ninja router to include global response schemas for all endpoints.
    """

    GLOBAL_RESPONSES = {
        500: ErrorResponseSchema,
        401: UnauthorizedResponseSchema,
        400: BadRequestResponseSchema,
        403: ForbiddenResponseSchema,
    }

    METHOD_SPECIFIC_RESPONSES = {
        Methods.POST: {422: ValidationErrorResponseSchema},
        Methods.PATCH: {404: NotFoundResponseSchema},
        Methods.GET: {404: NotFoundResponseSchema},
    }

    def __init__(
        self,
        *,
        permissions: Union[List[BasePermission], BasePermission] = None,
        response: Any = NOT_SET,
        **kwargs,
    ):
        self.permissions = permissions
        self.response = response
        super().__init__(**kwargs)
        http_methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]

        for method in http_methods:
            setattr(self, method.lower(), self._bind_methods(method.upper()))

    def _merge_permissions(self, permissions):
        global_permissions = self.permissions

        if not global_permissions:
            return permissions or []
        if not permissions:
            return global_permissions or []

        global_perm = (
            global_permissions if isinstance(global_permissions, list) else [global_permissions]
        )
        method_perm = permissions if isinstance(permissions, list) else [permissions]
        permissions_dict = {p.__class__.__name__: p for p in global_perm}
        permissions_dict.update({p.__class__.__name__: p for p in method_perm})
        return list(permissions_dict.values())

    def _bind_methods(self, method):
        def method_handler(
            self,
            path,
            permissions: Union[List[BasePermission], BasePermission] = None,
            response: Any = NOT_SET,
            **kwargs,
        ):
            """
            This is a handler that overrides the default method handler (get, post, put, patch, delete)
            It adds `permissions` parameter to check permissions for the endpoint

            Since the default calls self.api_operation but doesn't include `permissions` parameter, I am
            overriding it here to include `permissions` parameter.

            @router.get("/my-endpoint", permissions=[IsAuthenticated])
            """
            permissions = self._merge_permissions(permissions)
            return self.api_operation(
                [method], path, response=response, permissions=permissions, **kwargs
            )

        return types.MethodType(method_handler, self)

    def api_operation(
        self,
        methods: List[str],
        path: str,
        *,
        response: Any = NOT_SET,
        permissions: Union[List[BasePermission], BasePermission] = None,
        **kwargs,
    ):
        """
        Override the default api operation so that it can:
            - Add global response: It adds default response schema so I do not have to repeat for all endpoints
            - Add `permission` parameter: This adds permission parameter to endpoint so permissions can be checked
        """
        processed_response = self._process_response_with_globals(response, methods)

        def decorator(view_func: Any):
            @wraps(view_func)
            def wrapped_view_func(*view_args, **view_kwargs):
                request = view_args[0]
                if permissions:
                    check_permissions(request, permissions, view_func)
                return view_func(*view_args, **view_kwargs)

            self.add_api_operation(
                path, methods, wrapped_view_func, response=processed_response, **kwargs
            )
            return wrapped_view_func

        return decorator

    def _process_response_with_globals(self, response: Any, methods: List[str]) -> Any:
        """Process the response parameter to add global response schemas"""
        global_responses = self.GLOBAL_RESPONSES.copy()
        if isinstance(response, dict):
            global_responses.update(response)
        for method in methods:
            method_upper = method.upper()
            try:
                method_enum = Methods(method_upper)
                if method_enum in self.METHOD_SPECIFIC_RESPONSES:
                    global_responses.update(self.METHOD_SPECIFIC_RESPONSES[method_enum])
            except ValueError:
                pass

        if response is NOT_SET or response is None:
            return global_responses

        if isinstance(response, dict):
            processed_response = response.copy()
            for status_code, model in global_responses.items():
                if status_code not in processed_response:
                    processed_response[status_code] = model
            return processed_response
        else:
            processed_response = {200: response}
            for status_code, model in global_responses.items():
                if status_code not in processed_response:
                    processed_response[status_code] = model
            return processed_response
