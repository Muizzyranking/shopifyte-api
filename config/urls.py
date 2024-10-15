from django.contrib import admin
from django.urls import path
from users.api import auth_router, user_router, vendor_router
from ninja_jwt.controller import NinjaJWTDefaultController
from ninja_extra import NinjaExtraAPI

api = NinjaExtraAPI()
api.register_controllers(NinjaJWTDefaultController)
api.add_router("/auth/", auth_router)
api.add_router("/users/", user_router)
api.add_router("/vendors/", vendor_router)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
