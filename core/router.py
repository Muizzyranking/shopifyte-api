from typing import Any, List

from ninja import Router
from ninja.constants import NOT_SET

from core.schema import (
    ErrorResponseSchema,
    ForbiddenResponseSchema,
    UnauthorizedResponseSchema,
    ValidationErrorResponseSchema,
)


class CustomRouter(Router):
    """
    Modified ninja router to include global response schemas for all endpoints.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._global_responses = {
            500: ErrorResponseSchema,
            401: UnauthorizedResponseSchema,
            403: ForbiddenResponseSchema,
        }
        self._method_specific_responses = {
            "POST": {422: ValidationErrorResponseSchema},
        }

    def api_operation(self, methods: List[str], path: str, *, response: Any = NOT_SET, **kwargs):
        processed_response = self._process_response_with_globals(response, methods)
        return super().api_operation(methods, path, response=processed_response, **kwargs)

    def _process_response_with_globals(self, response: Any, methods: List[str]) -> Any:
        """Process the response parameter to add global response schemas"""
        global_responses = self._global_responses.copy()
        for method in methods:
            method_upper = method.upper()
            if method_upper in self._method_specific_responses:
                global_responses.update(self._method_specific_responses[method_upper])

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
