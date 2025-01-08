from django.contrib import admin
from django.shortcuts import render
from django.urls import path
from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController

from users.api import router as user_router

# from ninja import NinjaAPI

api = NinjaExtraAPI()
api.register_controllers(NinjaJWTDefaultController)
api.add_router("/users", user_router)


def home(request):
    return render(request, "index.html")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("", home),
]
