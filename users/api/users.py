from ninja import Router
from ninja_jwt.authentication import JWTAuth
from users.models import User
from users.schema import NotFoundSchema, UpdateUserSchema, UserSchema

router = Router()
jwt_auth = JWTAuth()


# api/users/me - current user profile
@router.get("/me", auth=jwt_auth, response={200: UserSchema})
def profile(request):
    return request.auth


# api/users/me - update current user profile
@router.put("/me", auth=jwt_auth,
            response={
                200: UserSchema,
                400: NotFoundSchema,
                401: NotFoundSchema
            })
def update_profile(request, data: UpdateUserSchema):
    user = request.auth

    if not user:
        return 401, {"message": "Authentication required"}

    try:
        for key, value in data.dict(exclude_unset=True).items():
            setattr(user, key, value)
        user.save()
        return 200, user

    except Exception as e:
        return 400, {"message": str(e)}


# api/users/me - delete current user profile
@router.delete("/me", auth=jwt_auth, response={204: None})
def delete_user(request):
    user = request.auth
    if not user:
        return 401, {"message": "Authentication required"}
    user.delete()
    return 204, None


# api/users/{username} - get user by username
@router.get("/{usernmae}", response={
    200: UserSchema,
    404: NotFoundSchema
})
def get_user(request, username: str):
    try:
        user = User.objects.get(username__iexact=username)
        return 200, user
    except User.DoesNotExist:
        return 404, {"message": "User not found"}
