from enum import Enum
from typing import Any, List

from ninja import Router
from ninja.constants import NOT_SET

from core.schema import (
    ErrorResponseSchema,
    ForbiddenResponseSchema,
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
        403: ForbiddenResponseSchema,
    }

    METHOD_SPECIFIC_RESPONSES = {
        Methods.POST: {422: ValidationErrorResponseSchema},
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def api_operation(self, methods: List[str], path: str, *, response: Any = NOT_SET, **kwargs):
        processed_response = self._process_response_with_globals(response, methods)
        return super().api_operation(methods, path, response=processed_response, **kwargs)

    def _process_response_with_globals(self, response: Any, methods: List[str]) -> Any:
        """Process the response parameter to add global response schemas"""
        global_responses = self.GLOBAL_RESPONSES.copy()
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
