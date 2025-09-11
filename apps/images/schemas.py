from typing import Optional

from ninja import ModelSchema, Schema
from pydantic import field_validator

from core.schemas import PaginatedResponseSchema

from .models import Image, ImageCategory


class ImageUploadSchema(Schema):
    category: ImageCategory = ImageCategory.UNCATEGORIZED
    alt_text: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

    @field_validator("category")
    def validate_category(cls, value):
        if value not in ImageCategory.choices:
            return ImageCategory.UNCATEGORIZED
        return value


class ImageResponseSchema(ModelSchema):
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    class Meta:
        model = Image
        fields = [
            "id",
            "title",
            "mime_type",
            "format",
            "alt_text",
            "title",
            "description",
            "height",
            "width",
        ]

    @staticmethod
    def resolve_url(image: Image) -> str:
        return image.url

    @staticmethod
    def resolve_thumbnail_url(image: Image) -> str:
        return image.thumbnail


class ImageTransformParams(Schema):
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    quality: Optional[int] = None


class ImagesResponse(PaginatedResponseSchema[ImageResponseSchema]):
    message: str = "Images retrieved successfully"
