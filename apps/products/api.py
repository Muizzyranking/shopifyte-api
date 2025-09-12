from ninja import Query
from apps.products.services import ProductService
from core.router import CustomRouter

from .schemas import ProductDetailSchema, ProductFilters, ProductListSchema

products_router = CustomRouter()


@products_router.get("", response=ProductListSchema)
def get_products(request, filters: Query[ProductFilters]):
    """
    Get a list of products.
    """
    result = ProductService.get_products(request, filters)
    return result


@products_router.get("{slug}", response={200: ProductDetailSchema})
def get_product_details(request, slug: str):
    return 200, {
        "message": "Product successfully retrieved",
        "data": ProductService.get_product_by_slug(slug),
    }
