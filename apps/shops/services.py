from django.http import HttpRequest

from core.cache import Cache
from core.pagination import Paginator
from core.utils import get_seconds

from .models import Shop, ShopProfile, ShopStatus
from .schemas import ShopSchema
from .utils import send_shop_welcome_email

shop_list_cache = Cache(prefix="shop_list", timeout=get_seconds(minutes=15))


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
