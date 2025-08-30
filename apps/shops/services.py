from apps.shops.utils import send_shop_welcome_email
from .models import Shop, ShopProfile


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
    send_shop_welcome_email(request, user, shop)
    return shop
