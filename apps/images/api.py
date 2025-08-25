import hashlib
import uuid

from django.http import HttpRequest, HttpResponse
from ninja import File, Query, UploadedFile

from core.auth import AuthBearer
from core.router import Router
from core.schema import SuccessResponseSchema

from .schemas import ImageResponseSchema, ImageTransformParams, ImageUploadSchema
from .services import ImageService

img_router = Router(tags=["images"])


@img_router.get("", auth=AuthBearer(), response={200: list[ImageResponseSchema]})
def get_images(request: HttpRequest):
    images = ImageService.get_user_images(request)
    return images


@img_router.post(
    "/upload",
    auth=AuthBearer(),
    response={200: ImageResponseSchema},
)
def upload_image(request: HttpRequest, file: File[UploadedFile], data: ImageUploadSchema):
    """
    Upload image
    """
    image = ImageService.upload_image(request=request, file=file, data=data or {})
    return image


@img_router.get("/{image_id}", response={200: ImageResponseSchema})
def get_image(request: HttpRequest, image_id: uuid.UUID):
    image = ImageService.get_image(image_id)
    return image


@img_router.delete("/{image_id}", auth=AuthBearer(), response={200: SuccessResponseSchema})
def delete_image(request: HttpRequest, image_id: uuid.UUID):
    image = ImageService.get_image(image_id)
    ImageService.delete_image(image, request)
    return "Image deleted successfully."


@img_router.get("/serve/{image_id}", url_name="serve_image")
def serve_image(request, image_id: uuid.UUID, parameters: Query[ImageTransformParams]):
    """Serve an image with optional transformations"""
    image = ImageService.get_image(image_id)
    content, content_type = ImageService.get_image_file(image, parameters)

    data = parameters.dict()
    has_transforms = any(v is not None and v != "" for v in data.values())
    etag = f"{image.file_hash}"
    cache_control = "public, max-age=31536000, immutable"
    if has_transforms:
        transform_key = f"w{parameters.width or ''}_h{parameters.height or ''}_f{parameters.format or ''}_q{parameters.quality}"
        etag_content = f"{image.file_hash}_{transform_key}"
        etag = hashlib.md5(etag_content.encode()).hexdigest()
        cache_control = "public, max-age=604800, stale-while-revalidate=86400"

    response = HttpResponse(content, content_type=content_type)
    response["Cache-Control"] = cache_control
    response["ETag"] = f'"{etag}"'
    response["Content-Disposition"] = f'inline; filename="{image.filename}"'
    return response
