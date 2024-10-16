from typing import Optional

from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from helpers.utils import send_verification_email
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import RefreshToken
from users.models import Store, User
from users.schema import (
    LoginSchema,
    NotFoundSchema,
    RegisterUserSchema,
    StoreSchema,
    TokenSchema,
    UserSchema,
)

router = Router()
jwt_auth = JWTAuth()


# /api/auth/verify_email/{uid}/{token}
@router.get("/verify_email/{uid}/{token}", response={
    200: None,
    400: NotFoundSchema
})
def verify_email(request, uid: int, token: str):
    """
    Verify a user's email address.

    Args:
        request: The HTTP request object.
        uid (int): The user's ID.
        token (str): The verification token.

    Returns:
        tuple: A tuple containing the status code and response data.
            - (200, None) if the email is successfully verified.
            - (400, {"message": str}) if an error occurs during verification.
    """
    try:
        user = User.objects.get(id=uid)
        if default_token_generator.check_token(user, token):
            user.email_verified = True
            user.save()
            return 200, None
    except Exception as e:
        return 400, {"message": str(e)}


# /api/auth/register/
@router.post("/register/",
             response={201: UserSchema, 400: NotFoundSchema})
# pyright: reportUnusedParameter=false
def register(request, data: RegisterUserSchema):
    """
    Register a new user.

    Args:
        request: The HTTP request object.
        data (RegisterUserSchema): The user registration data.

    Returns:
        tuple: A tuple containing the status code and response data.
            - (201, UserSchema) if the user is successfully registered.
            - (400, {"message": str}) if an error occurs during registration.
    """
    try:
        if User.objects.filter(email=data.email).exists():
            return 400, {"message": "Email already registered"}
        if User.objects.filter(username=data.username).exists():
            return 400, {"message": "Username already taken"}

        user = User.objects.create(
            email=data.email,
            username=data.username,
            first_name=data.first_name,
            last_name=data.last_name,
            street=data.street,
            city=data.city,
            country=data.country,
            zipcode=data.zipcode,
            phone_number=data.phone_number
        )
        user.set_password(data.password)
        user.is_active = False
        user.save()

        try:
            send_verification_email(request, user)
        except Exception as e:
            user.delete()
            return 400, {
                "message": f"Failed to send verification email {str(e)}"
            }

        user_data = {
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "street": user.street,
            "city": user.city,
            "country": user.country,
            "zipcode": user.zipcode,
            "phone_number": user.phone_number,
            "message": "Registration successful.\
            Please check your email for verification."
        }

        return 201, user_data
    except Exception as e:
        return 400, {"message": str(e)}


@router.post("/store/register", auth=jwt_auth,
             response={
                 201: StoreSchema,
                 400: NotFoundSchema,
                 409: NotFoundSchema
             })
def register_store(request, data: StoreSchema):
    """
   Register a new store for an authenticated user.

   Args:
       request: The HTTP request object.
       data (StoreSchema): The store registration data.

   Returns:
       tuple: A tuple containing the status code and response data.
           - (201, StoreSchema) if the store is successfully registered.
           - (400, {"message": str}) if an error occurs during registration\
                   or the user's email is not verified.
           - (409, {"message": str}) if the user already has a store.
   """
    user = request.auth
    if not user:
        return 400, {"message": "Authentication required"}

    if user.has_store:
        return 409, {"message": "User already has a store"}

    if not user.email_verified:
        return 400, {"message": "Email not verified"}

    try:
        store = Store.objects.create(
            user=user,
            store_name=data.store_name,
            store_desc=data.store_desc,
            store_street=data.store_street,
            store_city=data.store_city,
            store_country=data.store_country,
            store_zipcode=data.store_zipcode,
        )
        user.has_store = True
        user.save()
        return 201, store
    except Exception as e:
        return 400, {"message": str(e)}


@router.post("/login/", response={
    200: TokenSchema,
    401: NotFoundSchema,
    400: NotFoundSchema
})
def login(request, data: LoginSchema):
    """
    Authenticate a user and generate access and refresh tokens.

    Args:
        request: The HTTP request object.
        data (LoginSchema): The login credentials.

    Returns:
        tuple: A tuple containing the status code and response data.
            - (200, TokenSchema) if authentication is successful.
            - (401, {"message": str}) if authentication fails.
            - (400, {"message": str}) if an error occurs during\
                    token generation.
    """
    user: Optional[User] = authenticate(
        email=data.email, password=data.password)  # type: ignore

    if user is None:
        return 401, {"message": "Invalid Username or Password"}

    if user:
        refresh = RefreshToken.for_user(user)

        try:
            return {
                "email": user.email,
                "refresh": str(refresh),
                "access": str(refresh.access_token)  # type: ignore
            }
        except Exception as e:
            return 400, {"message": f"An error occurred {str(e)}"}
