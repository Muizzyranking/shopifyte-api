from django.http import HttpRequest

from apps.shops.exceptions import ShopNotFound
from apps.users.utils import get_user_from_request
from core.cache import Cache
from core.pagination import Paginator
from core.utils import get_seconds

from .models import Shop, ShopProfile, ShopStatus
from .schemas import ShopSchema
from .utils import send_shop_welcome_email

shop_list_cache = Cache(prefix="shop_list", timeout=get_seconds(minutes=15))
shop_detail_cache = Cache(prefix="shop_detail", timeout=get_seconds(minutes=30))


def create_shop_for_user(request, shop_data, user):
    shop = Shop.objects.create(
        owner=user,
        name=shop_data.name,
        description=shop_data.description,
        email=shop_data.email,
        address_line=shop_data.address_line,
        city=shop_data.city,
        state=shop_data.state,
        postal_code=shop_data.postal_code,
        country=shop_data.country,
    )
    ShopProfile.objects.create(shop=shop)
    shop_list_cache.clear()
    send_shop_welcome_email(request, user, shop)
    return shop


def get_all_shops(request: HttpRequest, filters, pagination):
    pagination = pagination.dict() if hasattr(pagination, "dict") else {}
    filters = filters.dict() if hasattr(filters, "dict") else {}
    page_size = pagination.get("page_size", 10)
    page_number = pagination.get("page", 1)
    cache_key_data = {
        "page_size": page_size,
        "page": page_number,
        **filters,
    }
    cache_key = shop_list_cache.generate_key(cache_key_data, suffix="all_shops")
    cache_response = shop_list_cache.get(cache_key)
    if cache_response:
        return cache_response

    queryset = Shop.objects.select_related("profile", "profile__logo").filter(
        status=ShopStatus.ACTIVE
    )
    paginator = Paginator(
        request=request, queryset=queryset, page_size=page_size, schema=ShopSchema
    )
    result = paginator.get_page(page_number)
    shop_list_cache.set(cache_key, result)
    return result


def get_shop_by_slug(shop_slug: str):
    try:
        key = shop_detail_cache.generate_key({"shop_slug": shop_slug})
        cached_shop = shop_detail_cache.get(key)
        if cached_shop:
            return cached_shop
        shop = Shop.objects.select_related("profile", "profile__logo").get(slug=shop_slug)
        shop_detail_cache.set(key, shop)
        return shop
    except Shop.DoesNotExist:
        raise ShopNotFound("Shop with the given slug does not exist.")
    except Exception:
        raise


def update_shop_for_user(request, shop_slug, data):
    user = get_user_from_request(request)

    try:
        shop = Shop.objects.get(slug=shop_slug, owner=user)
        shop_fields = [
            "name",
            "slug",
            "description",
            "email",
            "address_line",
            "city",
            "state",
            "postal_code",
            "country",
        ]
        shop_profile_fields = [
            "phone",
            "website_url",
            "facebook_url",
            "instagram_url",
            "twitter_url",
        ]
        data_dict = data.dict() if hasattr(data, "dict") else {}

        shop_data = {k: v for k, v in data_dict.items() if k in shop_fields}
        profile_data = {k: v for k, v in data_dict.items() if k in shop_profile_fields}

        if shop_data.get("slug"):
            existing_shop = Shop.objects.filter(slug=shop_data["slug"]).exclude(id=shop.id)
            if existing_shop.exists():
                raise ValueError("The provided slug is already in use by another shop.")

        for field, value in shop_data.items():
            if value is not None and hasattr(shop, field):
                setattr(shop, field, value)
        shop.save()

        if profile_data:
            for field, value in profile_data.items():
                if value is not None and hasattr(shop.profile, field):
                    setattr(shop.profile, field, value)
            shop.profile.save()

        shop_list_cache.clear()
        shop_detail_key = shop_detail_cache.generate_key({"shop_slug": shop_slug})
        shop_detail_cache.delete(shop_detail_key)
        return shop
    except Shop.DoesNotExist:
        raise ShopNotFound("Shop not found or you do not have permission to update it.")
    except Exception:
        raise
