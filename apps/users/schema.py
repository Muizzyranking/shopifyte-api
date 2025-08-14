from typing import Optional
from ninja import ModelSchema, Schema, Field
from pydantic import EmailStr, field_validator, model_validator

from core.schema import DataResponseSchema

from .models import CustomUser


class RegisterInput(Schema):
    """
    Schema for user registration input
    """

    email: EmailStr = Field(..., examples=["user@email.com"], description="User's email address")
    username: Optional[str] = Field(
        ..., examples=["john_doe"], description="Unique username for the user"
    )
    first_name: str = Field(..., examples=["John"], description="Unique username for the user")
    last_name: str = Field(..., examples=["Doe"], description="Unique username for the user")
    phone_number: str = Field(..., examples=["Doe"], description="Unique username for the user")
    password: str = Field(..., examples=["strongpassword123"], description="User's password")
    confirm_password: str = Field(
        ..., examples=["strongpassword123"], description="Confirmation of the user's password"
    )

    @field_validator("username")
    def validate_username(cls, v: str) -> str:
        if CustomUser.objects.filter(username=v).exists():
            raise ValueError("Username already exists")
        return v

    @field_validator("email")
    def email_unique(cls, v: str) -> str:
        if CustomUser.objects.filter(email=v).exists():
            raise ValueError("Email is already in use.")
        return v

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class LoginInput(Schema):
    email: EmailStr = Field(..., examples=["user@gmail.com"], description="User's email address")
    password: str = Field(..., examples=["strongpassword123"], description="User's password")


class LoginResponse(Schema):
    """
    Schema for login response
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")


class LoginDataReponse(DataResponseSchema[LoginResponse]):
    message: str = "Login successful"


class RefreshTokenSchema(Schema):
    """
    Schema for refresh token input
    """

    refresh_token: str = Field(..., description="JWT refresh token")


class UserProfile(ModelSchema):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "phone_number",
            "email_verified",
        ]


class UserProfileResponse(DataResponseSchema[UserProfile]):
    message: str = "User profile retrieved successfully"


class UpdateProfileSchema(Schema):
    """
    Schema for updating user profile
    """

    first_name: Optional[str] = Field(None, examples=["John"], description="User's first name")
    last_name: Optional[str] = Field(None, examples=["Doe"], description="User's last name")
    phone_number: Optional[str] = Field(
        None, examples=["1234567890"], description="User's phone number"
    )
    username: Optional[str] = Field(None, examples=["john_doe"], description="User's username")
