import hashlib
import io
from typing import Union
from uuid import UUID

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.http import Http404, HttpRequest
from PIL import Image as PILImage

from apps.users.models import CustomUser
from apps.users.utils import get_user_from_request
from core.cache import Cache
from core.pagination import Paginator
from core.utils import get_seconds

from .models import Image, ImageCategory, ImageFormat
from .schemas import ImageResponseSchema


class ImageProcessor:

    @classmethod
    def allowed_formats(cls):
        return {choices[0] for choices in ImageFormat.choices}

    @classmethod
    def allowed_mime_types(cls):
        return {ImageFormat.get_mime_type(fmt) for fmt in cls.allowed_formats()}

    @staticmethod
    def calculate_hash(file: bytes):
        return hashlib.sha256(file).hexdigest()

    @staticmethod
    def get_image_info(image: PILImage.Image):
        return {
            "format": image.format.lower() if image.format else "unknown",
            "mode": image.mode,
            "size": image.size,
            "width": image.width,
            "height": image.height,
        }

    @staticmethod
    def optimize_image(image: PILImage.Image, target_format: ImageFormat, quality: int = 85):
        if target_format not in ImageProcessor.allowed_formats():
            raise ValueError(f"Unsupported target format: {target_format}")

        output = io.BytesIO()

        if target_format == ImageFormat.JPEG and image.mode in ("RGBA", "P"):
            background = PILImage.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
            image = background

        save_kwargs = {"format": target_format, "optimize": True}
        if target_format == "JPEG":
            save_kwargs["quality"] = quality
            save_kwargs["progressive"] = True
        elif target_format == "PNG":
            save_kwargs["compress_level"] = 6
        elif target_format == "WEBP":
            save_kwargs["quality"] = quality
            save_kwargs["method"] = 6

        image.save(output, **save_kwargs)
        output.seek(0)
        return output

    @staticmethod
    def resize_image(image: PILImage.Image, width: int, height: int):
        image.thumbnail((width, height), PILImage.Resampling.LANCZOS)
        return image


class ImageService:

    FILE_SIZE_LIMIT = 10 * 1024 * 1024

    user_images_cache = Cache(prefix="user_images", timeout=get_seconds(minutes=10))
    image_cache = Cache(prefix="image_cache", timeout=get_seconds(minutes=30))
    image_transform_cache = Cache(prefix="image_transform", timeout=get_seconds(hours=1))

    @classmethod
    def get_format_info(cls, image: PILImage.Image):
        format = image.format.lower() if image.format else "unknown"

        if not format or format not in ImageProcessor.allowed_formats():
            raise ValueError(f"Unsupported image format: {format}")

        mine_type = ImageFormat.get_mime_type(format)
        return format, mine_type

    @classmethod
    def upload_image(
        cls,
        request: HttpRequest,
        file: UploadedFile,
        data,
    ):
        user: CustomUser = get_user_from_request(request)
        data = data.dict(exclude_unset=True) if hasattr(data, "dict") else data
        category = data.get("category", ImageCategory.UNCATEGORIZED)
        alt_text = data.get("alt_text", "")
        title = data.get("title", "")
        description = data.get("description", "")
        if file.size and file.size > cls.FILE_SIZE_LIMIT:
            raise ValueError("File size exceeds the maximum limit.")
        file_content = file.read()
        file.seek(0)

        file_hash = ImageProcessor.calculate_hash(file_content)
        existing_image = Image.objects.filter(file_hash=file_hash).first()

        if existing_image:
            return existing_image

        try:
            pil_image = PILImage.open(file)
            image_info = ImageProcessor.get_image_info(pil_image)
            format, mime_type = cls.get_format_info(pil_image)
        except Exception:
            raise ValueError("Invalid image file.")

        file_extension = ImageFormat.get_extension(mime_type)
        optimized_image_io = ImageProcessor.optimize_image(pil_image, format)
        optmized_content = optimized_image_io.getvalue()
        file_size = len(optmized_content)
        filename = f"{file_hash}.{file_extension}"
        upload_path = f"media/images/{category}/{filename}"
        save_path = default_storage.save(upload_path, ContentFile(optmized_content))
        image = Image.objects.create(
            uploaded_by=user,
            filename=filename,
            file_path=save_path,
            file_size=file_size,
            file_hash=file_hash,
            mime_type=mime_type,
            format=format,
            width=image_info["width"],
            height=image_info["height"],
            alt_text=alt_text,
            title=title,
            description=description,
        )
        image.url = image.get_url(request)
        image.save(update_fields=["url"])
        return image

    @classmethod
    def get_image(cls, image: Union[UUID, str, Image]) -> Image:
        if isinstance(image, Image):
            return image
        try:
            return Image.objects.get(id=image)
        except Image.DoesNotExist:
            raise Http404("Image not found")
        except Exception:
            raise

    @classmethod
    def get_user_images(cls, request: HttpRequest, query):
        user = get_user_from_request(request)
        query_params = query.dict(exclude_unset=True) if query else {}
        page = query_params.get("page", 1)
        page_size = query_params.get("page_size", 10)

        key_data = {
            "page": page,
            "page_size": page_size,
        }
        cache_key = cls.user_images_cache.generate_key(key_data, suffix=f"user_{str(user.id)}")
        cached_response = cls.user_images_cache.get(cache_key)

        if cached_response:
            return cached_response

        queryset = Image.objects.filter(uploaded_by=user).order_by("-created_at")
        paginator = Paginator(
            request, queryset=queryset, page_size=page_size, schema=ImageResponseSchema
        )
        page_obj = paginator.get_page(page)
        cls.user_images_cache.set(cache_key, page_obj)
        return page_obj

    @classmethod
    def get_image_file(cls, image: Image | UUID, transform_data=None):
        """Get image file content and content type"""
        image = cls.get_image(image)
        if not default_storage.exists(image.file_path):
            raise FileNotFoundError("Image file not found")

        cache_key = None
        if transform_data is None:
            cache_key = cls.image_cache.generate_key({"file_hash": image.file_hash})
            cached_content = cls.image_cache.get(cache_key) if cache_key else None
            if cached_content:
                return cached_content

        if transform_data:
            transform_params = (
                transform_data.dict(exclude_unset=True)
                if hasattr(transform_data, "dict")
                else transform_data
            )
            return cls.transform_image(image, **transform_params)

        with default_storage.open(image.file_path, "rb") as f:
            content = f.read()
        result = (content, image.mime_type)
        if cache_key:
            cls.image_cache.set(cache_key, result)
        return result

    @classmethod
    def transform_image(
        cls,
        image: Image,
        target_format: ImageFormat = None,
        width: int = None,
        height: int = None,
        quality: int = 85,
    ):
        image = cls.get_image(image)
        if not default_storage.exists(image.file_path):
            raise FileNotFoundError("Image file not found")
        transform_params = {
            "target_format": target_format,
            "width": width,
            "height": height,
            "quality": quality,
        }
        cache_key = cls.image_transform_cache.generate_key(transform_params, suffix=image.file_hash)
        cached_content = cls.image_transform_cache.get(cache_key)

        if cached_content:
            return cached_content

        with default_storage.open(image.file_path, "rb") as f:
            pil_image = PILImage.open(f)
            pil_image.load()

        if width or height:
            target_width = width if width else image.width
            target_height = height if height else image.height
            pil_image = ImageProcessor.resize_image(pil_image, target_width, target_height)

        target_format = target_format if target_format else image.format
        if not target_format or target_format not in ImageProcessor.allowed_formats():
            raise ValueError(f"Unsupported target format: {target_format}")
        mime_type = ImageFormat.get_mime_type(target_format)

        optimized_image_io = ImageProcessor.optimize_image(pil_image, target_format, quality)
        content = optimized_image_io.getvalue()
        result = (content, mime_type)
        cls.image_transform_cache.set(cache_key, result)
        return result

    @classmethod
    def update_image_metadata(
        cls,
        image: Image,
        alt_text: str = None,
        title: str = None,
        description: str = None,
    ):
        image = cls.get_image(image)
        if alt_text is not None:
            image.alt_text = alt_text
        if title is not None:
            image.title = title
        if description is not None:
            image.description = description
        image.save()
        return image

    def delete_image(self, image: Image, request):
        user = get_user_from_request(request)
        if image.uploaded_by != user:
            raise PermissionError("You do not have permission to delete this image.")
        image.delete()
