from ninja import Schema, Field
from typing import Dict, Generic, List, Optional, TypeVar

T = TypeVar("T", bound=Schema)


class BaseSchema(Schema):
    message: str


class SuccessResponseSchema(BaseSchema):
    message: str = "Success"


class ErrorResponseSchema(BaseSchema):
    message: str = "Error"


class DataResponseSchema(BaseSchema, Generic[T]):
    data: T


class ValidationErrorResponseSchema(BaseSchema):
    message: str = Field(..., example="Invalid data")
    errors: Dict[str, List[str]] = Field(
        ..., example={"email": ["invalid email"], "username": ["must be at least 3 characters"]}
    )


class UnauthorizedResponseSchema(BaseSchema):
    message: str = "Authentication required"


class ForbiddenResponseSchema(BaseSchema):
    message: str = "Permission denied"


class NotFoundResponseSchema(BaseSchema):
    message: str = "Resource not found"


class BadRequestResponseSchema(BaseSchema):
    message: str = "Bad request"


class PaginatedResponseSchema(BaseSchema, Generic[T]):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    page: int
    page_size: int = 10
    total_pages: int
    data: List[T]


class PaginatedQueryParams(Schema):
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Number of items per page")
