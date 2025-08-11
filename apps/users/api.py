from core.auth import AuthBearer
from core.exceptions.email import EmailSendError
from core.exceptions.verification import EmailMisMatch, UserNotFound
from core.router import CustomRouter
from core.schema import (
    BadRequestResponseSchema,
    NotFoundResponseSchema,
    SuccessResponseSchema,
)
from core.utils import error_message, response_message, response_with_data

from .models import CustomUser
from .schema import LoginDataReponse, LoginInput, RefreshTokenSchema, RegisterInput
from .services import (
    authenticate_user,
    create_user,
    make_token_for_user,
    refresh_tokens_from_refresh_token,
    verify_email_token,
)
from .utils import send_confirmation_email

auth_router = CustomRouter(tags=["Auth"])


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
    response={
        200: SuccessResponseSchema,
        400: BadRequestResponseSchema,
        404: NotFoundResponseSchema,
    },
)
def verify_email(request, token: str):
    try:
        response = verify_email_token(token)
        return 200, response_message(response)
    except UserNotFound as e:
        return 404, error_message(e)
    except (ValueError, EmailMisMatch) as e:
        return 400, error_message(e)
    except Exception as e:
        return 500, error_message(e)


@auth_router.post("login", response={200: LoginDataReponse, 400: BadRequestResponseSchema})
def login(request, data: LoginInput):
    try:
        user: CustomUser = authenticate_user(data.email, data.password)
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
