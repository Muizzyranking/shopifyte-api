from datetime import datetime
from typing import Optional

from ninja import Schema
from pydantic import EmailStr, field_validator


class RegisterSchema(Schema):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    street: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    zipcode: Optional[int] = None
    phone_number: Optional[str] = None


class UserSchema(Schema):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    street: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    zipcode: Optional[int] = None
    phone_number: Optional[str] = None
    created_at: datetime
    email_verified: bool

    @field_validator("created_at")
    @classmethod
    def format_created_at(cls, value: datetime):
        return value.strftime("%Y-%m-%d")


class RegisterResponseSchema(Schema):
    data: UserSchema
    message: str


class ErrorSchema(Schema):
    message: str


class LoginSchema(Schema):
    email: EmailStr
    password: str


class TokenSchema(Schema):
    access_token: str
    token_type: str
    email: EmailStr
