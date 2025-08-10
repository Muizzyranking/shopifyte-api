from ninja_extra import NinjaExtraAPI
from apps.users.api import auth_router


class CustomNinjaAPI(NinjaExtraAPI):
    def create_response(self, request, data, *, status=200):
        """
        Overrides the default response creation to handle validation errors
        """
        if status == 422 and isinstance(data, dict) and "detail" in data:
            errors = {}
            if isinstance(data["detail"], list):
                for error in data["detail"]:
                    if isinstance(error, dict) and "loc" in error:
                        field = error["loc"][-1] if error["loc"] else "general"
                        message = error.get("ctx", {}).get("error", error.get("msg", ""))
                        message = message.replace("Value error, ", "")

                        if field not in errors:
                            errors[field] = []
                        errors[field].append(message)

            data = {"message": "Validation failed", "errors": errors}

        return super().create_response(request, data, status=status)


api = CustomNinjaAPI(
    title="SHOPIFYTE API Reference",
    description="API Reference for the SHOPIFYTE API",
    # docs_url=None,
    openapi_url="/schema.json",
    urls_namespace="api",
)

api.add_router("/auth/", auth_router)
