from typing import Optional
from ninja import Schema
from pydantic import EmailStr


class Meschema(Schema):
    username: str
    email: EmailStr
    is_authenticated: bool


class RegisterUserSchema(Schema):
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    phone_number: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    zipcode: Optional[int] = None


class UserSchema(Schema):
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    zipcode: Optional[int] = None
    message: Optional[str] = None
    email_verified: Optional[bool] = False


class UpdateUserSchema(Schema):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    zipcode: Optional[int] = None


class StoreSchema(Schema):
    store_name: str
    store_desc: str
    store_street: str
    store_city: str
    store_country: str
    store_zipcode: int


class UpdateStoreSchema(Schema):
    store_name: Optional[str] = None
    store_desc: Optional[str] = None
    store_street: Optional[str] = None
    store_city: Optional[str] = None
    store_country: Optional[str] = None
    store_zipcode: Optional[int] = None


class LoginSchema(Schema):
    email: str
    password: str


class TokenSchema(Schema):
    email: EmailStr
    refresh: str
    access: str


class NotFoundSchema(Schema):
    message: str
