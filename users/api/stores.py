
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from users.models import Store
from users.schema import (
    NotFoundSchema,
    StoreSchema,
    UpdateStoreSchema,
)

jwt_auth = JWTAuth()
router = Router()


# /api/stores/{store_slug} - get store profile
@router.get("/{store_slug}", response={
    200: StoreSchema,
    404: NotFoundSchema
})
def get_store(request, store_slug: str):
    try:
        store = Store.objects.get(store_slug__iexact=store_slug)
        return 200, store
    except Store.DoesNotExist:
        return 404, {"message": "Store not found"}


# /api/stores/{store_slug} - update store profile
@router.put("/{store_slug}", auth=jwt_auth,
            response={
                200: StoreSchema,
                401: NotFoundSchema,
                403: NotFoundSchema
            })
def update_store_info(request, store_slug: str, data: UpdateStoreSchema):
    user = request.auth
    if not user:
        return 401, {"message": "Authentication required"}

    if not user.has_store:
        return 401, {"message": "Authentication required"}

    store = Store.objects.get(store_slug__iexact=store_slug)

    if not store.user == user:
        return 403, {"message": "Permission denied"}

    try:
        for key, value in data.dict(exclude_unset=True).items():
            setattr(store, key, value)
        store.save()
        return 200, store
    except Exception as e:
        return 400, {"message": str(e)}
