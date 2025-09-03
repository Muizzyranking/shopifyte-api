from typing import Optional
from ninja import Field, ModelSchema, Schema
from pydantic import EmailStr

from apps.images.schemas import ImageResponseSchema
from apps.shops.models import Shop, ShopProfile
from core.schema import PaginatedResponseSchema


class ShopCreateSchema(Schema):
    name: str = Field(..., examples=["My shop"], description="Name of the shop")
    description: Optional[str] = Field(
        None, examples=["This is my shop"], description="Description of the shop"
    )
    email: Optional[EmailStr] = Field(
        None, examples=["shop@example.com"], description="Contact email of the shop"
    )

    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class ShopFilters(Schema):
    status: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


class ShopSchema(ModelSchema):
    logo_url: Optional[str] = None

    class Meta:
        model = Shop
        fields = ["id", "name", "slug", "description", "city", "country"]

    @staticmethod
    def resolve_logo_url(obj):
        return obj.logo_url


class ShopListSchema(PaginatedResponseSchema[ShopSchema]):
    message: str = "Shops retrieved successfully"
