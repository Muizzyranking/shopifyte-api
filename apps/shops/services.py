from django.http import HttpRequest

from apps.images.models import ImageCategory
from apps.images.services import ImageService
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
    if Shop.objects.filter(owner=user).exists():
        raise ValueError("User already has a shop.")
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
    _clear_shop_cache()
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
        data_dict = data.dict(exclude_unset=True) if hasattr(data, "dict") else {}

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
            profile, _ = ShopProfile.objects.get_or_create(shop=shop)
            for field, value in profile_data.items():
                if value is not None and hasattr(profile, field):
                    setattr(shop.profile, field, value)
            profile.save()
        _clear_shop_cache(shop_slug)
        return shop
    except Shop.DoesNotExist:
        raise ShopNotFound("Shop not found or you do not have permission to update it.")
    except Exception:
        raise


def upload_logo_for_shop(request, shop_slug, logo):
    user = get_user_from_request(request)
    try:
        shop = Shop.objects.get(slug=shop_slug, owner=user)
        profile, _ = ShopProfile.objects.get_or_create(shop=shop)
        old_logo = profile.logo
        data = {"category": ImageCategory.LOGO, "title": f"{shop.name} Logo"}
        image = ImageService.upload_image(request, logo, data)
        profile.logo = image
        profile.save(update_fields=["logo", "updated_at"])
        _clear_shop_cache(shop_slug)

        if old_logo:
            try:
                ImageService.delete_image(old_logo, request)
            except Exception:
                pass  # do nothing

        return shop
    except Shop.DoesNotExist:
        raise ShopNotFound("Shop not found or you do not have permission to update it.")
    except Exception:
        raise


def delete_logo_for_shop(request, shop_slug):
    user = get_user_from_request(request)
    try:
        shop = Shop.objects.get(slug=shop_slug, owner=user)
        profile = getattr(shop, "profile", None)
        if profile and profile.logo:
            logo = profile.logo
            profile.logo = None
            ImageService.delete_image(logo, request)
            profile.save(update_fields=["logo", "updated_at"])
            _clear_shop_cache(shop_slug)
    except Exception:
        pass


def deactivate_shop_for_user(request, shop_slug):
    user = get_user_from_request(request)
    try:
        shop = Shop.objects.get(slug=shop_slug, owner=user)
        shop.status = ShopStatus.INACTIVE
        shop.save(update_fields=["status", "updated_at"])
        shop_list_cache.clear()
        shop_detail_key = shop_detail_cache.generate_key({"shop_slug": shop_slug})
        shop_detail_cache.delete(shop_detail_key)
    except Shop.DoesNotExist:
        raise ShopNotFound("Shop not found or you do not have permission to delete it.")
    except Exception:
        raise


def activate_shop_for_user(request, shop_slug):
    user = get_user_from_request(request)
    try:
        shop = Shop.objects.get(slug=shop_slug, owner=user)
        shop.status = ShopStatus.ACTIVE
        shop.save(update_fields=["status", "updated_at"])
        _clear_shop_cache(shop_slug)
    except Shop.DoesNotExist:
        raise ShopNotFound("Shop not found or you do not have permission to delete it.")
    except Exception:
        raise


def _clear_shop_cache(shop_slug: str = None) -> None:
    """Clear shop-related caches."""
    shop_list_cache.clear()
    if shop_slug:
        shop_detail_key = shop_detail_cache.generate_key({"shop_slug": shop_slug})
        shop_detail_cache.delete(shop_detail_key)
