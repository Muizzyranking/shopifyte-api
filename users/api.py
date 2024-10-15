from typing import Optional

from django.contrib.auth import authenticate
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import RefreshToken

from .models import User, Vendor
from .schema import (
    LoginSchema,
    NotFoundSchema,
    RegisterUserSchema,
    TokenSchema,
    UserSchema,
    VendorSchema,
)

auth_router = Router()
jwt_auth = JWTAuth()


@auth_router.post("/register/",
                  response={201: UserSchema, 400: NotFoundSchema})
def register(request, data: RegisterUserSchema):
    """
    Registers a new user
    """
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
            phone_number=data.phone_number
        )
        user.set_password(data.password)
        user.save()

        user_data = {
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "street": user.street,
            "city": user.city,
            "country": user.country,
            "zipcode": user.zipcode,
            "phone_number": user.phone_number
        }

        return 201, user_data
    except Exception as e:
        return 400, {"message": str(e)}


@auth_router.post("/vendoregister/",
                  response={201: VendorSchema, 400: NotFoundSchema})
def register_vendor(request, data: VendorSchema):
    """
    Registers a new vendor
    """
    user = request.auth
    if not user:
        return 400, {"message": "Authentication required"}

    if user.is_vendor:
        return 400, {"message": "User is already a vendor"}

    try:
        vendor = Vendor.objects.create(
            user=user,
            store_name=data.store_name,
            store_desc=data.store_desc,
            store_street=data.store_street,
            store_city=data.store_city,
            store_country=data.store_country,
            store_zipcode=data.store_zipcode,
        )
        user.is_vendor = True
        user.save()
        return 201, vendor
    except Exception as e:
        return 400, {"message": str(e)}


@auth_router.post("/login/", response={
    200: TokenSchema,
    401: NotFoundSchema,
    400: NotFoundSchema
})
def login(request, data: LoginSchema):
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
