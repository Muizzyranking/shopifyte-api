from typing import Optional
from ninja import Field, ModelSchema, Schema
from pydantic import EmailStr

from apps.images.schemas import ImageResponseSchema
from apps.shops.models import Shop
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
    logo: Optional[ImageResponseSchema] = None

    class Meta:
        model = Shop
        fields = ["id", "name", "slug", "description", "city", "country"]

    @staticmethod
    def resolve_logo(obj):
        return obj.logo_image


class ShopSchemaResponse(Schema):
    message: str = "Shop retrieved successfully"
    data: ShopSchema


class ShopListSchema(PaginatedResponseSchema[ShopSchema]):
    message: str = "Shops retrieved successfully"


class ShopLinks(Schema):
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twiiter_url: Optional[str] = None
    website: Optional[str] = None


class ShopDetailSchema(ModelSchema):
    logo_url: Optional[str] = None
    phone: Optional[str] = None
    links: Optional[ShopLinks] = None
    full_address: Optional[str] = None
    is_featured: Optional[bool] = None
    member_since: Optional[str] = None

    class Meta:
        model = Shop
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "email",
            "address_line",
            "city",
            "state",
            "postal_code",
            "country",
            "status",
            "created_at",
        ]

    @staticmethod
    def resolve_logo_url(obj):
        return obj.logo_url

    @staticmethod
    def resolve_owner_name(obj):
        return obj.owner.get_full_name() or obj.owner.username

    @staticmethod
    def resolve_phone(obj):
        return obj.profile.phone if hasattr(obj, "profile") and obj.profile else None

    @staticmethod
    def resolve_website_url(obj):
        return obj.profile.website_url if hasattr(obj, "profile") and obj.profile else None

    @staticmethod
    def resolve_full_address(obj):
        parts = [obj.address_line, obj.city, obj.state, obj.postal_code, obj.country]
        return ", ".join(filter(None, parts)) or None

    @staticmethod
    def resolve_links(obj):
        if hasattr(obj, "profile") and obj.profile:
            return {
                "facebook_url": obj.profile.facebook_url,
                "instagram_url": obj.profile.instagram_url,
                "twitter_url": obj.profile.twitter_url,
                "website": obj.profile.website,
            }
        return None

    @staticmethod
    def resolve_is_featured(obj):
        return obj.profile.is_featured if hasattr(obj, "profile") and obj.profile else False

    @staticmethod
    def resolve_member_since(obj):
        return obj.created_at.strftime("%B %Y")  # e.g., "January 2024"


class ShopDetailResponse(Schema):
    message: str = "Shop details retrieved successfully"
    data: ShopDetailSchema


class ShopUpdateSchema(Schema):
    # Shop fields
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    email: Optional[str] = None
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    # Profile fields
    phone: Optional[str] = None
    website_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
