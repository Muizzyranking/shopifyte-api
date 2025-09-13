from django.db.models import Prefetch, Q

from core.cache import Cache
from core.exceptions import NotFound
from core.pagination import Paginator
from core.utils import get_seconds

from .models import Product, ProductImages


class ProductService:
    cache = Cache(prefix="products", timeout=get_seconds(minutes=15))

    @classmethod
    def _clear_cache(cls, product_id=None, shop_id=None):
        patterns = [
            "product_list*",
        ]
        for pattern in patterns:
            cls.cache.delete_pattern(pattern)

        if product_id:
            key = cls.cache.generate_key({"slug": product_id})
            cls.cache.delete(key)
        if shop_id:
            key = cls.cache.generate_key({"shop_id": shop_id})
            cls.cache.delete(key)

    @staticmethod
    def _base_queryset(active: bool = True):
        return (
            Product.objects.select_related("shop", "category")
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=ProductImages.objects.select_related("image").filter(primary=True),
                    to_attr="prefetched_primary_image",
                ),
                Prefetch(
                    "images",
                    queryset=ProductImages.objects.select_related("image").filter(primary=False),
                    to_attr="prefetched_gallery_image",
                ),
            )
            .filter(is_active=active)
        )

    @classmethod
    def get_products(cls, request, filters):
        page = getattr(filters, "page", 1) if filters else 1
        page_size = getattr(filters, "page_size", 10) if filters else 10
        filters = filters.dict() if filters else {}
        cache_key_data = {
            "page": page,
            "page_size": page_size,
            **filters,
        }
        cache_key = cls.cache.generate_key(cache_key_data, suffix="product_list")

        cache_result = cls.cache.get(cache_key)
        if cache_result:
            return cache_result

        qs = cls._base_queryset()
        if filters:
            qs = cls._apply_filters(qs, filters)

        qs = qs.order_by("-created_at")

        paginator = Paginator(request, qs, page_size)
        result = paginator.get_page(page)
        cls.cache.set(cache_key, result)
        return result

    @classmethod
    def get_product_by_slug(cls, slug):
        cache_key = cls.cache.generate_key({"slug": slug})
        cached_product = cls.cache.get(cache_key)

        if cached_product:
            return cached_product

        try:
            qs = cls._base_queryset()
            product = qs.get(slug=slug)
            cls.cache.set(cache_key, product)
            return product
        except Product.DoesNotExist:
            raise NotFound("Product not found")

    @staticmethod
    def _apply_filters(queryset, filters):

        if not filters:
            return queryset

            # Price range filter
        if "min_price" in filters and filters["min_price"]:
            queryset = queryset.filter(price__gte=filters["min_price"])

        if "max_price" in filters and filters["max_price"]:
            queryset = queryset.filter(price__lte=filters["max_price"])

        # Category filter
        if "category_id" in filters and filters["category_id"]:
            queryset = queryset.filter(category_id=filters["category_id"])

        # Shop filter
        if "shop_id" in filters and filters["shop_id"]:
            queryset = queryset.filter(shop_id=filters["shop_id"])

        # Search filter
        if "search" in filters and filters["search"]:
            search_term = filters["search"]
            queryset = queryset.filter(
                Q(name__icontains=search_term) | Q(description__icontains=search_term)
            )

        # In stock filter
        if "in_stock_only" in filters and filters["in_stock_only"]:
            queryset = queryset.filter(stock__gt=0)

        return queryset
