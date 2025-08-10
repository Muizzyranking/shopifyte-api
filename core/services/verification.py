import base64
import hashlib
import hmac
import json
import time
from enum import Enum
from json import JSONDecodeError
from typing import Any, Dict
import uuid

from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse

from apps.users.models import CustomUser
from core.exceptions.verification import EmailMisMatch, TokenExpiredError, UserNotFound


class TokenType(Enum):
    CONFIRMATION = "confirmation"


class VerificationService:
    """Simple email verification service with self-contained tokens"""

    def __init__(self):
        self.secret_key = getattr(settings, "SECRET_KEY")
        if not self.secret_key:
            raise RuntimeError("SECRET_KEY must be set in Django settings")
        self.token_expiry_seconds = getattr(settings, "VERIFICATION_TIMEOUT", 86400)

    def generate_signature(self, payload_b64: str) -> str:
        return hmac.new(self.secret_key.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()

    def generate_token(self, user, token_type: TokenType) -> str:
        """
        Generate a self-contained verification token

        Args:
            user: User instance

        Returns:
            Encoded token string
        """
        if not isinstance(user, CustomUser):
            raise UserNotFound("Invalid user provided")

        payload = {
            "user_id": str(user.id),
            "email": user.email,
            "iat": int(time.time()),
            "exp": int(time.time()) + self.token_expiry_seconds,
            "type": token_type.value,
        }

        payload_json = json.dumps(payload, separators=(",", ":"))
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()

        signature = self.generate_signature(payload_b64)

        token = f"{payload_b64}.{signature}"
        return token

    def verify_token(self, token: str, token_type: TokenType) -> Dict[str, Any]:
        """
        Verify and decode a token

        Args:
            token: The token to verify

        Returns:
            Dict with verification result
        """
        try:
            payload_b64, signature = token.split(".", 1)
        except ValueError:
            raise ValueError("Invalid token format")

        expected_signature = self.generate_signature(payload_b64)

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid token signature")

        try:
            payload_json = base64.urlsafe_b64decode(payload_b64.encode()).decode()
            payload = json.loads(payload_json)
        except (ValueError, JSONDecodeError):
            raise ValueError("Invalid token payload")

        if time.time() > payload.get("exp", 0):
            raise TokenExpiredError("Token has expired")

        if payload.get("type") != token_type.value:
            raise ValueError("Token type mismatch")

        try:
            user_id = uuid.UUID(payload["user_id"])
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise UserNotFound("User not found")

        if user.email != payload["email"]:
            raise EmailMisMatch("Email has been changed since token was generated")
        return {"valid": True, "user": user, "payload": payload}

    @staticmethod
    def create_verification_url(request: HttpRequest, token: str, name: str) -> str:
        """
        Create verification URL with just the token (no user_id)

        Args:
            request: Django HttpRequest object
            token: Verification token

        Returns:
            Full verification URL
        """
        path = reverse(f"api:{name}", kwargs={"token": token})
        return request.build_absolute_uri(path)
