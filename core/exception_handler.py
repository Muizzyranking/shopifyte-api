import logging
from typing import Callable, Dict, List, Optional, Type, Union

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from ninja.errors import ValidationError
from ninja_extra import NinjaExtraAPI
from pydantic import ValidationError as PydanticValidationError

from core.exceptions.auth import Unauthorized

logger = logging.getLogger(__name__)


class APIExceptionHandler:
    """
    Centralized exception handler and easy exception registration.
    """

    def __init__(self, api: NinjaExtraAPI, debug: bool = None):
        self.api = api
        self.debug = debug if debug is not None else settings.DEBUG
        self._exception_registry = {}

    def create_error_response(
        self,
        request: HttpRequest,
        message: str,
        status: int = 400,
        errors: Optional[Dict[str, List[str]]] = None,
    ) -> HttpResponse:
        """Creates error response message"""
        response_data = {"message": message}

        if errors:
            response_data["errors"] = errors

        return self.api.create_response(request, response_data, status=status)

    @staticmethod
    def _get_field_name(location: Union[tuple, list, str]) -> str:
        """Extract clean field name from pydantic location"""
        if isinstance(location, str):
            location = (location,)
        if not location:
            return "general"

        skip_prefixes = {"body", "query", "path", "form", "header"}
        clean_location = [str(part) for part in location if str(part) not in skip_prefixes]

        return clean_location[-1] if clean_location else str(location[-1])

    @staticmethod
    def _get_clean_message(error: dict) -> str:
        """Convert pydantic error to user-friendly message"""
        error_type = error.get("type", "")
        msg = error.get("msg", "")
        ctx = error.get("ctx", {})

        if error_type == "value_error" and ctx and "error" in ctx:
            return str(ctx["error"])

        clean_msg = msg.replace("Value error, ", "").replace("Validation error, ", "")
        return clean_msg.capitalize() if clean_msg else "Invalid value"

    @staticmethod
    def _get_exception_message(
        exc: Exception, fallback_message: Optional[str] = None, force: bool = False
    ) -> str:
        """
        Extract message from exception, with fallback support

        Args:
            exc: The exception instance
            fallback_message: Fallback message if exception has no meaningful message
            force: uses fallback message even if exception has a message

        Returns:
            The exception message or fallback message
        """
        if force and fallback_message:
            return fallback_message

        exc_message = str(exc).strip()

        if exc_message and exc_message != type(exc).__name__:
            return exc_message

        if fallback_message:
            return fallback_message

        return f"An error occurred: {type(exc).__name__}"

    def _log_exception(self, request: HttpRequest, exc: Exception, status: int = 500):
        """Securely log exceptions with relevant context"""
        log_data = {
            "exception_type": type(exc).__name__,
            "status_code": status,
            "path": request.path,
            "method": request.method,
            "user_id": (
                getattr(request.user, "id", "anonymous") if hasattr(request, "user") else "unknown"
            ),
        }

        if hasattr(request, "request_id"):
            log_data["request_id"] = request.request_id

        if status >= 500:
            logger.error(f"Internal server error: {log_data}", exc_info=exc)
        elif status >= 400:
            logger.warning(f"Client error: {log_data}")

    def _is_output_validation_error(
        self, exc: Union[ValidationError, PydanticValidationError]
    ) -> bool:
        """
        Determine if this is an output validation error by examining the stack trace.
        This looks for Django Ninja's response processing in the call stack.
        """
        if "NinjaResponse" in str(exc):
            return True

        return False

    def _handle_output_validation_error(
        self, request: HttpRequest, exc: Union[ValidationError, PydanticValidationError]
    ) -> HttpResponse:
        self._log_exception(request, exc, 500)
        message = "An internal error occurred while processing."
        if self.debug:
            message = f"Response validation error: {self._get_exception_message(exc)}"

        return self.create_error_response(request=request, message=message, status=500)

    def _handle_input_validation_error(
        self, request: HttpRequest, exc: Union[ValidationError, PydanticValidationError]
    ) -> HttpResponse:
        """Handle validation errors with improved error aggregation"""
        errors = {}

        try:
            error_list = exc.errors() if callable(exc.errors) else exc.errors
        except Exception:
            error_list = []

        if error_list:
            for error in error_list:
                if isinstance(error, dict) and "loc" in error:
                    field = self._get_field_name(error.get("loc", []))
                    message = self._get_clean_message(error)

                    if field not in errors:
                        errors[field] = []
                    if message not in errors[field]:
                        errors[field].append(message)
                elif isinstance(error, str):
                    if "general" not in errors:
                        errors["general"] = []
                    if error not in errors["general"]:
                        errors["general"].append(error)

        main_message = self._get_exception_message(exc, "Invalid data provided", True)
        self._log_exception(request, exc, 422)
        return self.create_error_response(
            request=request,
            errors=errors,
            message=main_message,
            status=422,
        )

    def _handle_validation_error(
        self, request: HttpRequest, exc: Union[ValidationError, PydanticValidationError]
    ) -> HttpResponse:
        if self._is_output_validation_error(exc):
            return self._handle_output_validation_error(request, exc)
        return self._handle_input_validation_error(request, exc)

    def _handle_global_exception(self, request: HttpRequest, exc: Exception) -> HttpResponse:
        """Handle all other exceptions with security considerations"""
        self._log_exception(request, exc, 500)

        if self.debug:
            message = self._get_exception_message(exc, f"Internal server error: {str(exc)}")
        else:
            message = self._get_exception_message(
                exc, "An unexpected error occurred. Please try again later."
            )

        return self.create_error_response(request=request, message=message, status=500)

    def _setup_default_handlers(self):
        """Setup default exception handlers"""
        self.register_handler(ValidationError, self._handle_validation_error)
        self.register_handler(PydanticValidationError, self._handle_validation_error)

        self.register_handler(
            Unauthorized,
            self.create_custom_handler(
                fallback_message="Authentication required",
                status=401,
                log_level="warning",
            ),
        )

        self.register_handler(
            PermissionDenied,
            self.create_custom_handler(
                fallback_message="Permission denied",
                status=403,
                log_level="warning",
            ),
        )

        self.register_handler(
            Http404,
            self.create_custom_handler(
                fallback_message="Resource not found",
                status=404,
                log_level="info",
            ),
        )

        self.register_handler(Exception, self._handle_global_exception)

    def register_handler(
        self,
        exception_class: Type[Exception],
        handler: Callable[[HttpRequest, Exception], HttpResponse],
        override: bool = False,
    ):
        """
        Register a custom exception handler

        Args:
            exception_class: The exception class to handle
            handler: The handler function
            override: Whether to override existing handlers
        """
        if exception_class in self._exception_registry and not override:
            logger.warning(
                f"Handler for {exception_class.__name__} already exists. "
                f"Use override=True to replace it."
            )
            return

        self._exception_registry[exception_class] = handler
        self.api.add_exception_handler(exception_class, handler)
        logger.info(f"Registered exception handler for {exception_class.__name__}")

    def create_custom_handler(
        self,
        fallback_message: str,
        status: int,
        errors: Dict[str, List[str]] = None,
        log_level: str = "warning",
    ) -> Callable[[HttpRequest, Exception], HttpResponse]:
        """
        Create a simple custom handler with predefined response

        Args:
            message: Error message to return
            status: HTTP status code
            errors: Error dictionary
            log_level: Logging level for this exception
        """

        def handler(request: HttpRequest, exc: Exception) -> HttpResponse:
            self._log_exception(request, exc, status)
            message = self._get_exception_message(exc, fallback_message)
            return self.create_error_response(
                request=request, message=message, status=status, errors=errors
            )

        return handler

    def apply_handlers(self) -> NinjaExtraAPI:
        """Apply all registered handlers to the API"""
        self._setup_default_handlers()
        return self.api


def setup_exception_handlers(api: NinjaExtraAPI, debug: bool = None) -> NinjaExtraAPI:
    """
    Setup custom exception handlers for the API.

    Args:
        api: The NinjaExtraAPI instance
        debug: Whether to show debug information (defaults to settings.DEBUG)

    Returns:
        The API instance with handlers applied
    """
    excpetion_handler = APIExceptionHandler(api, debug)
    return excpetion_handler.apply_handlers()
