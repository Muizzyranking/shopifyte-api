from ninja import Router

from apps.users.schema import RegisterInput
from apps.users.services import create_user, verify_email_token
from apps.users.utils import send_confirmation_email
from core.exceptions.email import EmailSendError
from core.exceptions.verification import EmailMisMatch, UserNotFound
from core.schema import ErrorResponseSchema, SuccessResponseSchema
from core.utils import error_message, response_message

auth_router = Router(tags=["Auth"])


@auth_router.post(
    "/register",
    summary="Register a new user",
    response={
        200: SuccessResponseSchema,
        202: SuccessResponseSchema,
        400: ErrorResponseSchema,
        500: ErrorResponseSchema,
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
        404: ErrorResponseSchema,
        400: ErrorResponseSchema,
        500: ErrorResponseSchema,
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
