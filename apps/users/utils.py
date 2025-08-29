import random
import string
from django.http import HttpRequest
from django.urls import reverse

from apps.users.exceptions import UserNotFound
from apps.users.models import CustomUser
from core.services.email import EmailService
from core.services.token_service import TokenService, TokenType


def generate_code(length: int = 6) -> str:
    characters = string.digits
    return "".join(random.choices(characters, k=length))


def verification_url(request: HttpRequest, token: str):
    namespace = getattr(request.resolver_match, "namespace", None)
    path = reverse(f"{namespace}:verify_email", kwargs={"token": token})
    return request.build_absolute_uri(path)


def send_confirmation_email(request: HttpRequest, user: CustomUser):
    verification_service = TokenService()
    token = verification_service.generate_token(user, TokenType.CONFIRMATION)
    confirmation_url = verification_url(request, token)
    email_service = EmailService()
    return email_service.send_confirmation_email(user, confirmation_url)


def get_user_from_request(request: HttpRequest) -> CustomUser:
    """
    Retrieve the authenticated user from the request.
    """
    user = getattr(request, "auth", None)
    if not isinstance(user, CustomUser):
        raise UserNotFound("User not found or not authenticated.")
    return user
