from core.services.verification import TokenType, VerificationService
from .models import CustomUser


def create_user(user_data):
    user_data = user_data.dict()
    user = CustomUser.objects.create(
        email=user_data.get("email"),
        username=user_data.get("username", None),
        first_name=user_data.get("first_name"),
        last_name=user_data.get("last_name"),
        email_verified=False,
    )
    user.set_password(user_data.get("password"))
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
