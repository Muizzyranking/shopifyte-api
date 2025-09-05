import base64
import hashlib
import hmac
import json
import time
from enum import Enum

from django.conf import settings
from django.core.cache import cache

from apps.users.exceptions import UserNotFound
from apps.users.models import CustomUser
from core.exceptions import InvalidToken, TokenExpired


class TokenType(Enum):
    CONFIRMATION = "confirmation"
    PASSWORD_RESET = "password_reset"


class TokenService:
    def __init__(self):
        self.secret_key = getattr(settings, "VERIFICATION_SECRET_KEY", None) or getattr(
            settings, "SECRET_KEY"
        )
        self.token_expiry_seconds = {
            TokenType.CONFIRMATION: getattr(settings, "VERIFICATION_TIMEOUT", 86400),
            TokenType.PASSWORD_RESET: getattr(settings, "PASSWORD_RESET_TIMEOUT", 3600),
        }
        self.cache = cache

    @staticmethod
    def _get_cache_key(user_id: str, token_type: TokenType) -> str:
        """Generate cache key for tracking user's token by type"""
        return f"user_token:{user_id}:{token_type.value}"

    def _get_token_expiry(self, token_type: TokenType) -> int:
        """Get expiry time for specific token type"""
        return self.token_expiry_seconds.get(token_type, 3600)

    @staticmethod
    def _validate_token_type(token_type: TokenType | str) -> TokenType:
        if isinstance(token_type, str):
            try:
                token_type = TokenType(token_type)
            except ValueError:
                raise InvalidToken(f"Invalid token type: {token_type}")

        if not isinstance(token_type, TokenType):
            raise InvalidToken(f"Invalid token type: {token_type}")

        return token_type

    def generate_signature(self, payload_b64: str) -> str:
        return hmac.new(self.secret_key.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()

    def generate_token(self, user, token_type: TokenType | str):
        if not isinstance(user, CustomUser):
            raise UserNotFound("Invalid user provided")

        token_type = self._validate_token_type(token_type)
        user_id = str(user.id)
        cache_key = self._get_cache_key(user_id, token_type)
        self.cache.delete(cache_key)
        iat = int(time.time())
        token_exp = self._get_token_expiry(token_type)
        exp = iat + token_exp
        payload = {
            "user_id": user_id,
            "email": user.email,
            "iat": iat,
            "exp": exp,
            "type": token_type.value,
        }
        payload_json = json.dumps(payload, separators=(",", ":"))
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()
        signature = self.generate_signature(payload_b64)
        self.cache.set(cache_key, payload, timeout=token_exp)
        token = f"{payload_b64}.{signature}"
        return token

    def verify_token(self, token: str, token_type: TokenType | str):
        try:
            payload_b64, signature = token.split(".", 1)
        except ValueError:
            raise InvalidToken("Invalid token format")
        expected_signature = self.generate_signature(payload_b64)

        if not hmac.compare_digest(expected_signature, signature):
            raise InvalidToken("Invalid token signature")

        try:
            payload_json = base64.urlsafe_b64decode(payload_b64).decode()
            payload = json.loads(payload_json)
        except (ValueError, json.JSONDecodeError):
            raise InvalidToken("Invalid token payload")

        if time.time() > payload.get("exp", 0):
            raise TokenExpired("Token has expired")

        user_id = payload.get("user_id")
        expected_type = self._validate_token_type(token_type)
        token_type_value = payload.get("type")

        if token_type_value != expected_type.value:
            raise InvalidToken(
                f"Token type mismatch: expected {expected_type.value}, got {token_type_value}"
            )

        cache_key = self._get_cache_key(user_id, expected_type)
        cached_payload = self.cache.get(cache_key)

        if cached_payload is None:
            raise TokenExpired("Token has been used or expired")

        self.cache.delete(cache_key)

        try:
            user = CustomUser.objects.get(id=payload["user_id"])
            if user.email != payload["email"]:
                raise InvalidToken("Email mismatch in token payload")

            return {"user": user, "valid": True}
        except CustomUser.DoesNotExist:
            raise UserNotFound("User not found")
        except Exception as e:
            raise ValueError(f"Error retrieving user: {str(e)}") from e
