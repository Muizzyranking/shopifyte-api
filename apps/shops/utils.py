from apps.users.models import CustomUser
from core.services.email import EmailService, EmailType

from .models import Shop


def send_shop_welcome_email(request, user: CustomUser, shop: Shop):
    context = {
        "name": user.get_full_name(),
        "shop_name": shop.name,
        "shop_url": request.build_absolute_uri(shop.get_url()),
        "dashboard_url": request.build_absolute_uri("/dashboard/shops"),
    }
    return EmailService().send_email(EmailType.SHOP_WECLOME, [user.email], context)
