from ninja import Schema
from typing import Dict, Generic, List, TypeVar

T = TypeVar("T")


class BaseSchema(Schema):
    message: str


class SuccessResponseSchema(BaseSchema):
    message: str = "Success"


class ErrorResponseSchema(BaseSchema):
    message: str = "Error"


class DataResponseSchema(BaseSchema, Generic[T]):
    data: T


class ValidationErrorResponseSchema(BaseSchema):
    message: str = "Invalid data"
    errors: Dict[str, List[str]]


class UnauthorizedResponseSchema(BaseSchema):
    message: str = "Authentication required"


class ForbiddenResponseSchema(BaseSchema):
    message: str = "Permission denied"


class NotFoundResponseSchema(BaseSchema):
    message: str = "Resource not found"


class BadRequestResponseSchema(BaseSchema):
    message: str = "Bad request"
