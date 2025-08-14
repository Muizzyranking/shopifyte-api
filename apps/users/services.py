from tokenize import TokenError
from django.contrib.auth import authenticate
from django.http import HttpRequest
from ninja_jwt.tokens import RefreshToken
from core.exceptions.auth import Unauthorized
from core.exceptions.verification import UserNotFound
from core.services.verification import TokenType, VerificationService
from .models import CustomUser


def create_user(user_data):
    user_data = user_data.dict()
    password = user_data.pop("password")
    user = CustomUser.objects.create(**user_data)
    user.set_password(password)
    user.save()
    return user


def update_user(request: HttpRequest, update_data) -> CustomUser:
    user = get_user_from_request(request)
    user_data = update_data.dict(exclude_unset=True)
    # remove email and password
    user_data.pop("password", None)
    user_data.pop("email", None)
    for key, value in user_data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    user.save()
    return user


def verify_email_token(token: str) -> str:
    verification_service = VerificationService()
    data = verification_service.verify_token(token, TokenType.CONFIRMATION)
    if not data["valid"]:
        raise ValueError("Invalid or expired token.")
    user_data = data["user"]
    user = CustomUser.objects.filter(id=user_data.id, email=user_data.email).first()
    if not user:
        raise ValueError("Invalid token or user not found.")
    if user.email_verified:
        raise ValueError("Email is already verified.")
    user.email_verified = True
    user.save()
    return "Email verification successful. You can now log in."


def authenticate_user(email: str, password: str) -> CustomUser:
    """
    Authenticate user with email and password.

    Args:
        email (str): User's email.
        password (str): User's password.

    Returns:
        Authenticated user object.

    Raises:
        Unauthorized: If authentication fails.
    """
    user = authenticate(email=email, password=password)
    if user is None:
        raise Unauthorized("Invalid email or password.")
    return user


def make_token_for_user(user: CustomUser):
    """
    Create a verification token for the user.

    Args:
        user (CustomUser): The user for whom the token is created.
        token_type (TokenType): The type of token to create.

    Returns:
        str: The generated token.
    """
    token = RefreshToken.for_user(user)
    return {
        "access_token": str(token.access_token),
        "refresh_token": str(token),
    }


def refresh_tokens_from_refresh_token(refresh_token_str: str) -> dict:
    """
    Validate refresh token string and return a new access token.
    """
    try:
        refresh = RefreshToken(refresh_token_str)
    except TokenError:
        raise Unauthorized("Invalid or expired refresh token")

    access = str(refresh.access_token)

    return {"access": access, "refresh": None}
