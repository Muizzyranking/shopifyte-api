from ninja import Schema
from typing import Generic, List, TypeVar

T = TypeVar("T")


class BaseSchema(Schema):
    message: str


class SuccessResponseSchema(BaseSchema):
    message: str = "Success"


class ErrorResponseSchema(BaseSchema):
    message: str = "Error"


class DataResponseSchema(BaseSchema, Generic[T]):
    data: List[T]
