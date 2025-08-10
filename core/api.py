from ninja_extra import NinjaExtraAPI
from apps.users.api import auth_router


api = NinjaExtraAPI(
    title="SHOPIFYTE API Reference",
    description="API Reference for the SHOPIFYTE API",
    # docs_url=None,
    openapi_url="/schema.json",
    urls_namespace="api",
)

api.add_router("/auth/", auth_router)
