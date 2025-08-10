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
