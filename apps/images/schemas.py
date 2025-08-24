from typing import Optional

from ninja import ModelSchema, Schema
from pydantic import field_validator

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

    class Meta:
        model = Image
        fields = [
            "id",
            "title",
            "view_count",
            "url",
            "mime_type",
        ]


class ImageTransformParams(Schema):
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    quality: Optional[int] = None
