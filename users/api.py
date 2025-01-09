from django.contrib.auth import authenticate
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import RefreshToken

from users.models import User
from users.schema import (
    ErrorSchema,
    LoginSchema,
    RegisterResponseSchema,
    RegisterSchema,
    TokenSchema,
)

router = Router()
jwt_auth = JWTAuth()


@router.get("/")
def home(request):
    return {"message": "Hello World"}


@router.post(
    "/auth/register",
    response={201: RegisterResponseSchema, 400: ErrorSchema},
)
def register(request, data: RegisterSchema):
    """
    Registers a new user

    Args:

        request: the HTTP request object
        data: (RegisterSchema) the registeration data

    Returns:

        tuple containing the status codea and the response message:
        - (201, UserSchema) if the user is created succesfully
        - (400, {"message": str}) if the user already exists
        - (400, {"message": str}) for any other error
    """

    if User.objects.filter(email=data.email).exists():
        return 400, {"message": "Email already exists"}
    if User.objects.filter(username=data.username).exists():
        return 400, {"message": "Username already exists"}

    try:
        user = User.objects.create(
            email=data.email,
            username=data.username,
            first_name=data.first_name,
            last_name=data.last_name,
            street=data.street,
            city=data.city,
            country=data.country,
            zipcode=data.zipcode,
            phone_number=data.phone_number,
        )
        user.set_password(data.password)
        user.email_verified = False
        user.save()

        user_data = {
            "data": {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "street": user.street,
                "city": user.city,
                "country": user.country,
                "zipcode": user.zipcode,
                "phone_number": user.phone_number,
                "email_verified": user.email_verified,
            },
            "message": "Registration successful.\
            Please check your email for verification.",
        }

        return 201, user_data
    except Exception as e:
        return 400, {"message": str(e)}


@router.get(
    "/auth/login", auth=jwt_auth, response={200: TokenSchema, 400: ErrorSchema}
)
def login(request, data: LoginSchema):
    """
    Login route for user

    This routes authenticates the user and returns a token


    Args:

        data: LoginSchema object containing the email and password

    Return:

        -(200, TokenSchema) if the user is authenticated successfully
        -(400, {"message": str}) if the user is not authenticated
    """
    try:
        user: User | None = authenticate(
            email=data.email, password=data.password
        )  # type: ignore
        if user is None:
            return 400, {"message": "Invalid credentials"}

        refresh = RefreshToken.for_user(user)
        try:
            token_data = {
                "refresh": str(refresh),
                "access": str(refresh.access_token),  # type: ignore
                "email": user.email,
            }
            return 200, token_data
        except Exception as e:
            return 400, {"message": str(e)}

    except Exception as e:
        return 400, {"message": str(e)}
