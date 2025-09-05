from django.http import HttpRequest
from ninja import File, Query, UploadedFile

from apps.users.utils import get_user_from_request
from core.auth import AuthBearer
from core.router import CustomRouter as Router
from core.schema import PaginatedQueryParams, SuccessResponseSchema
from core.utils import response_message, response_with_data

from .schemas import (
    ShopCreateSchema,
    ShopDetailResponse,
    ShopFilters,
    ShopListSchema,
    ShopSchemaResponse,
    ShopUpdateSchema,
)
from .services import (
    activate_shop_for_user,
    create_shop_for_user,
    deactivate_shop_for_user,
    delete_logo_for_shop,
    get_all_shops,
    get_shop_by_slug,
    update_shop_for_user,
    upload_logo_for_shop,
)

shop_router = Router(tags=["shops"])


@shop_router.post("", auth=AuthBearer(), response={200: SuccessResponseSchema})
def create_shop(request, data: ShopCreateSchema):
    user = get_user_from_request(request)
    create_shop_for_user(request, data, user)
    return response_message("Shop created successfully")


@shop_router.get("", response={200: ShopListSchema})
def get_shops(
    request: HttpRequest,
    filters: Query[ShopFilters] = None,
    pagination: Query[PaginatedQueryParams] = None,
):
    return get_all_shops(request, filters, pagination)


@shop_router.get("/{shop_slug}", response=ShopDetailResponse)
def get_shop(request: HttpRequest, shop_slug: str):
    data = get_shop_by_slug(shop_slug)
    return response_with_data("Shop details retrieved successfully", data=data)


@shop_router.patch("/{shop_slug}", auth=AuthBearer(), response={200: SuccessResponseSchema})
def update_shop(request, shop_slug: str, data: ShopUpdateSchema):
    update_shop_for_user(request, shop_slug, data)
    return response_message("Shop updated successfully")


@shop_router.post("/{shop_slug}/logo", auth=AuthBearer(), response={200: ShopSchemaResponse})
def upload_shop_logo(request: HttpRequest, logo: File[UploadedFile], shop_slug: str):
    shop = upload_logo_for_shop(request, shop_slug, logo)
    return 200, response_with_data("Image uploaded successfully", data=shop)


@shop_router.delete("/{shop_slug}/logo", auth=AuthBearer(), response={200: SuccessResponseSchema})
def delete_shop_logo(request: HttpRequest, shop_slug: str):
    delete_logo_for_shop(request, shop_slug)
    return 200, response_message("Logo deleted successfully")


@shop_router.delete(
    "/{shop_slug}/deactivate", auth=AuthBearer(), response={200: SuccessResponseSchema}
)
def deactivate_shop(request: HttpRequest, shop_slug: str):
    deactivate_shop_for_user(request, shop_slug)
    return 200, response_message("Shop has been deactivated successfully")


@shop_router.patch(
    "/{shop_slug}/activate", auth=AuthBearer(), response={200: SuccessResponseSchema}
)
def activate_shop(request: HttpRequest, shop_slug: str):
    activate_shop_for_user(request, shop_slug)
    return 200, response_message("Shop has been activated successfully")
