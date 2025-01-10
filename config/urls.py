from django.contrib import admin
from django.shortcuts import render
from django.urls import path
from ninja import Router
from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController

from users.api import auth_router, user_router

hello_router = Router()


# from ninja import NinjaAPI
@hello_router.get("/")
def hello_world(request):
    return {"message": "Hello World"}


api = NinjaExtraAPI()
api.register_controllers(NinjaJWTDefaultController)
api.add_router("/auth", auth_router)
api.add_router("/users", user_router)
api.add_router("/", hello_router)


def home(request):
    return render(request, "index.html")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("", home),
]
