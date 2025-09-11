from typing import Union

from django.db.models import Prefetch

from core.pagination import Paginator

from .models import Product, ProductImages
from .schemas import ProductFilters


def get_all_products(request, filters: Union[ProductFilters, None] = None):
    page = getattr(filters, "page", 1) if filters else 1
    page_size = getattr(filters, "page_size", 10) if filters else 10
    qs = (
        Product.objects.select_related("shop", "category")
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImages.objects.select_related("image").filter(primary=True),
                to_attr="prefetched_primary_image",
            )
        )
        .filter(is_active=True)
        .order_by("-created_at")
    )
    qs = filter_products(qs, filters)

    paginator = Paginator(request, qs, page_size=page_size)
    return paginator.get_page(page)


def filter_products(qs, filters):
    if filters:
        if filters.category:
            qs = qs.filter(category__name__iexact=filters.category)

        if filters.search:
            qs = qs.filter(name__icontains=filters.search)

        if filters.shop:
            qs = qs.filter(shop__name__iexact=filters.shop)

        if filters.min_price is not None:
            qs = qs.filter(price__gte=filters.min_price)

        if filters.max_price is not None:
            qs = qs.filter(price__lte=filters.max_price)

        if filters.in_stock is True:
            qs = qs.filter(stock__gt=0)

        if filters.on_sale is True:
            qs = qs.filter(discount_price__isnull=False)

        if filters.sort == "price_asc":
            qs = qs.order_by("price")
        elif filters.sort == "price_desc":
            qs = qs.order_by("-price")

    return qs
