from ninja_extra import NinjaExtraAPI

from apps.shops.api import shop_router
from apps.users.api import auth_router, profile_router
from apps.images.api import img_router
from core.exception_handler import setup_exception_handlers


class CustomNinjaExtraAPI(NinjaExtraAPI):
    pass


api = CustomNinjaExtraAPI(
    title="SHOPIFYTE API Reference",
    description="API Reference for the SHOPIFYTE API",
    # docs_url=None,
    openapi_url="/schema.json",
    urls_namespace="api",
)


api = setup_exception_handlers(api)

api.add_router("/auth", auth_router)
api.add_router("/profile", profile_router)
api.add_router("/images", img_router)
api.add_router("/shops", shop_router)
