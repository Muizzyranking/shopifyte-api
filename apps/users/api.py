from apps.users.exceptions import UserNotFound
from core.auth import AuthBearer
from core.exceptions import EmailSendError
from core.permissions import BasePermission
from core.router import CustomRouter
from core.schema import (
    BadRequestResponseSchema,
    ErrorResponseSchema,
    SuccessResponseSchema,
)
from core.utils import error_message, response_message, response_with_data

from .models import CustomUser
from .schemas import (
    ChangePasswordSchema,
    ConfirmResetPassword,
    LoginDataReponse,
    LoginInput,
    RefreshTokenSchema,
    RegisterInput,
    ResendVerification,
    ResetPasswordSchema,
    UpdateEmailSchema,
    UpdateProfileSchema,
    UserProfileResponse,
)
from .services import (
    authenticate_user,
    change_user_password,
    confirm_reset_password,
    create_user,
    make_token_for_user,
    refresh_tokens_from_refresh_token,
    reset_user_password,
    update_user_email,
    update_user_profile,
    verify_email_token,
)
from .utils import get_user_from_request, send_confirmation_email

auth_router = CustomRouter(tags=["auth"])
profile_router = CustomRouter(tags=["profile"], auth=AuthBearer())


@auth_router.post(
    "/register",
    summary="Register a new user",
    response={
        200: SuccessResponseSchema,
        202: SuccessResponseSchema,
        400: BadRequestResponseSchema,
    },
)
def register_user(request, user_data: RegisterInput):
    try:
        user = create_user(user_data)
        send_confirmation_email(request, user)
        return 200, response_message(
            "User registered successfully. Please check your email for confirmation."
        )
    except EmailSendError:
        return 202, response_message("Registration successful. Email confirmation is pending.")
    except ValueError as e:
        return 400, error_message(e)
    except Exception as e:
        return 500, error_message(e)


@auth_router.get(
    "verify-email/{token}",
    url_name="verify_email",
    summary="Verify user email",
    response={200: SuccessResponseSchema},
)
def verify_email(request, token: str):
    response = verify_email_token(token)
    return 200, response_message(response)


@auth_router.post("/resend-verification", response={200: SuccessResponseSchema})
def resend_verification(request, payload: ResendVerification):
    try:
        user = get_user_from_request(request)
        send_confirmation_email(request, user)
    except UserNotFound:
        payload_dict = payload.dict()
        email = payload_dict.get("email")
        if not email:
            return 400, error_message("Email is required to resend verification.")
        user = CustomUser.objects.filter(email=email).first()
        send_confirmation_email(request, user)
    except EmailSendError:
        return 202, response_message("Email verification is pending.")
    return 200, response_message("Verification email resent successfully.")


@auth_router.post("login", response={200: LoginDataReponse, 400: BadRequestResponseSchema})
def login(request, data: LoginInput):
    try:
        user = authenticate_user(data.email, data.password)
        token = make_token_for_user(user)
        return 200, response_with_data("Login successful", token)
    except ValueError as e:
        return 400, error_message(e)


@auth_router.post(
    "refresh-token",
    response={
        200: dict,
        400: BadRequestResponseSchema,
    },
)
def refresh_token(request, data: RefreshTokenSchema):
    token = refresh_tokens_from_refresh_token(data.refresh_token)

    return 200, response_with_data("Token refreshed successfully", token)


@auth_router.post("/reset-password/request", response=SuccessResponseSchema)
def request_password_reset(request, data: ResetPasswordSchema):
    reset_user_password(request, data)
    return 200, response_message("Password reset email sent successfully.")


@auth_router.post(
    "/reset-password/confirm/{token}",
    response={200: SuccessResponseSchema, 400: ErrorResponseSchema},
)
def confirm_password_reset(request, token: str, data: ConfirmResetPassword):
    confirm_reset_password(request, token, data)
    return 200, response_message("Password reset successful.")


@profile_router.get("", response={200: UserProfileResponse})
def get_profile(request):
    user: CustomUser = get_user_from_request(request)
    return 200, response_with_data("Profile retrieved successfully", user)


@profile_router.patch("", response={200: UserProfileResponse})
def update_profile(request, user_data: UpdateProfileSchema):
    user = update_user_profile(request, user_data)
    return 200, response_with_data("Profile updated successfully", user)


@profile_router.patch(
    "/email",
    response={
        200: SuccessResponseSchema,
        202: SuccessResponseSchema,
    },
)
def update_email(request, user_data: UpdateEmailSchema):
    try:
        user = update_user_email(request, user_data)
        if not user.email_verified:
            send_confirmation_email(request, user)
        return 200, response_message(
            "Email updated successfully. Please check your email for confirmation."
        )
    except EmailSendError:
        return 202, response_message("Email updated successfully. Email verification is pending.")


@profile_router.patch("/password", response=SuccessResponseSchema)
def change_password(request, payload: ChangePasswordSchema):
    change_user_password(request, payload)
    return 200, response_message("Password changed successfully.")
