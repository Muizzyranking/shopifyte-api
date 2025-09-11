from ninja import Query
from apps.products.services import get_all_products
from core.router import CustomRouter

from .schemas import ProductFilters, ProductListSchema

products_router = CustomRouter()


@products_router.get("", response=ProductListSchema)
def get_products(request, filters: Query[ProductFilters]):
    """
    Get a list of products.
    """
    result = get_all_products(request, filters)
    return result
