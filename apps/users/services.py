from tokenize import TokenError

from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.http import HttpRequest
from ninja_jwt.tokens import RefreshToken

from apps.users.utils import get_user_from_request
from core.exceptions import Unauthorized
from core.exceptions import InvalidToken
from core.services.email import EmailService, EmailType
from core.services.token_service import TokenService, TokenType

from .models import CustomUser


def create_user(user_data):
    user_data = user_data.dict()
    password = user_data.pop("password")
    user_data.pop("confirm_password")
    user = CustomUser.objects.create(**user_data)
    user.set_password(password)
    user.save()
    return user


def update_user_profile(request: HttpRequest, update_data) -> CustomUser:
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


def update_user_email(request: HttpRequest, email_data) -> CustomUser:
    user = get_user_from_request(request)
    email_data = email_data.dict()
    email = email_data.get("email")
    new_email = (email or "").strip().lower()
    current_email = (user.email or "").strip().lower()
    if new_email == current_email:
        return user
    try:
        validate_email(new_email)
    except DjangoValidationError:
        raise ValueError("Invalid email address.")

    if CustomUser.objects.filter(email=new_email).exclude(id=user.id).exists():
        raise ValueError("Email is already in use.")

    user.email = email
    user.email_verified = False
    user.save(update_fields=["email", "email_verified"])
    return user


def verify_email_token(token: str) -> str:
    verification_service = TokenService()
    data = verification_service.verify_token(token, TokenType.CONFIRMATION)
    if not data.get("valid", False):
        raise ValueError("Invalid or expired token.")
    user_data = data["user"]
    user = CustomUser.objects.filter(id=user_data.id, email=user_data.email).first()
    if not user:
        raise ValueError("Invalid token or user not found.")
    if user.email_verified:
        raise ValueError("Email is already verified.")
    user.email_verified = True
    user.save()
    return "Email verification successful."


def change_user_password(request: HttpRequest, password_data):
    user = get_user_from_request(request)
    data = password_data.dict()
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_new_password")
    old_password = data.get("old_password")
    if not user.check_password(old_password):
        raise ValueError("Old password is incorrect.")
    if new_password != confirm_password:
        raise ValueError("New passwords do not match.")
    user.set_password(new_password)
    user.save(update_fields=["password"])
    return user


def reset_user_password(request, data):
    data = data.dict()
    email = data.get("email")
    try:
        user: CustomUser = CustomUser.objects.get(email=email)
        verification_service = TokenService()
        email_service = EmailService()
        token = verification_service.generate_token(user, TokenType.PASSWORD_RESET)
        context = {"name": user.get_full_name(), "reset_url": token}
        email_service.send_email(
            email_type=EmailType.PASSWORD_RESET,
            to_emails=[user.email],
            context=context,
        )
    except CustomUser.DoesNotExist:
        # log errror
        pass


def confirm_reset_password(request: HttpRequest, token: str, data):
    data = data.dict()
    new_password = data.get("new_password")
    try:
        verification_service = TokenService()
        verification_result = verification_service.verify_token(token, TokenType.PASSWORD_RESET)

        if not verification_result["valid"]:
            raise InvalidToken("Invalid token")

        user: CustomUser = verification_result["user"]
        if user.check_password(new_password):
            raise ValueError("New password cannot be the same as the old password.")
        user.set_password(new_password)
        user.save(update_fields=["password"])
    except Exception:
        raise


def authenticate_user(email: str, password: str):
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
