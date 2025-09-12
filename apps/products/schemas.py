from typing import List, Literal, Optional

from ninja import ModelSchema, Schema

from apps.images.schemas import ImageResponseSchema
from core.schemas import BaseSchema, PaginatedQueryParams, PaginatedResponseSchema

from .models import Product


class ProductFilters(PaginatedQueryParams):
    search: Optional[str] = None
    category: Optional[str] = None
    shop: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    in_stock: Optional[bool] = None
    on_sale: Optional[bool] = None
    sort: Optional[Literal["price_asc", "price_desc"]] = None


class ProductImageSchema(Schema):
    url: Optional[str]
    alt_text: Optional[str]
    title: Optional[str]
    description: Optional[str]
    primary: bool


class ProductSchema(ModelSchema):
    product_image: Optional[ImageResponseSchema] = None

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "discount_price",
            "stock",
            "is_active",
            "slug",
            "created_at",
            "updated_at",
        ]

    @staticmethod
    def resolve_product_image(obj):
        return obj.primary_image


class ProductListSchema(PaginatedResponseSchema[ProductSchema]):
    message: str = "Product retrieved successfully"


class ShortShopInfo(Schema):
    name: Optional[str] = None
    slug: Optional[str] = None


class ProductDetail(ModelSchema):
    shop: Optional[ShortShopInfo] = None
    product_image: Optional[ImageResponseSchema] = None
    gallery_images: Optional[List[ImageResponseSchema]] = None

    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "discount_price", "stock", "slug"]

    @staticmethod
    def resolve_shop(obj):
        return obj.shop

    @staticmethod
    def resolve_product_image(obj):
        return obj.primary_image

    @staticmethod
    def resolve_gallery_images(obj):
        return obj.gallery_images


class ProductDetailSchema(BaseSchema):
    data: ProductDetail
