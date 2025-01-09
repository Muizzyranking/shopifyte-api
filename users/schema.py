from ninja import Schema
from pydantic import EmailStr
from typing import Optional


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
    street: Optional[str]
    city: Optional[str]
    country: Optional[str]
    zipcode: Optional[int]
    phone_number: Optional[str]
    created_at: str
    email_verified: bool


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
