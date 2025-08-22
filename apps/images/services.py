import hashlib
import io

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from PIL import Image as PILImage
from django.http import Http404

from apps.users.models import CustomUser

from .models import Image, ImageCategory, ImageFormat


class ImageProcessor:
    MAX_SIZE = 1024

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
    def __init__(self):
        self.file_size = 20
        self.processor = ImageProcessor()
        pass

    def get_format_info(self, image: PILImage.Image):
        format = image.format.lower() if image.format else "unknown"

        if not format or format not in self.processor.allowed_formats():
            raise ValueError(f"Unsupported image format: {format}")

        mine_type = ImageFormat.get_mime_type(format)
        return format, mine_type

    def upload_image(
        self,
        user: CustomUser,
        file: UploadedFile,
        data,
    ):
        data = data.dict(exclude_unset=True) if hasattr(data, "dict") else data
        category = data.get("category", ImageCategory.UNCATEGORIZED)
        alt_text = data.get("alt_text", "")
        title = data.get("title", "")
        description = data.get("description", "")
        if file.size and file.size > self.file_size:
            raise ValueError("File size exceeds the maximum limit.")
        file_content = file.read()
        file.seek(0)

        file_hash = self.processor.calculate_hash(file_content)
        existing_image = Image.objects.filter(file_hash=file_hash).first()

        if existing_image:
            return existing_image

        try:
            pil_image = PILImage.open(file)
            image_info = self.processor.get_image_info(pil_image)
            format, mime_type = self.get_format_info(pil_image)
        except Exception:
            raise ValueError("Invalid image file.")

        file_extension = ImageFormat.get_extension(mime_type)
        optimized_image_io = self.processor.optimize_image(pil_image, format)
        optmized_content = optimized_image_io.getvalue()
        file_size = len(optmized_content)
        filename = f"{file_hash}.{file_extension}"
        upload_path = f"images/{category}/{filename}"
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
        return image

    def get_image(self, image_id):
        try:
            Image.objects.get(id=image_id)
        except Image.DoesNotExist:
            raise Http404("Image not found")
        except Exception:
            raise

    def get_image_file(self, image: Image, transform_data):
        """Get image file content and content type"""
        if not default_storage.exists(image.file_path):
            raise FileNotFoundError("Image file not found")
        if transform_data:
            transform_params = (
                transform_data.dict(exclude_unset=True)
                if hasattr(transform_data, "dict")
                else transform_data
            )
            return self.transform_image(image, **transform_params)
        with default_storage.open(image.file_path, "rb") as f:
            content = f.read()
        return content, image.mime_type

    def transform_image(
        self,
        image: Image,
        target_format: ImageFormat = None,
        width: int = None,
        height: int = None,
        quality: int = 85,
    ):
        if not default_storage.exists(image.file_path):
            raise FileNotFoundError("Image file not found")
        with default_storage.open(image.file_path, "rb") as f:
            pil_image = PILImage.open(f)
            pil_image.load()

        if width or height:
            target_width = width if width else image.width
            target_height = height if height else image.height
            pil_image = self.processor.resize_image(pil_image, target_width, target_height)

        target_format = target_format if target_format else image.format
        if not target_format or target_format not in self.processor.allowed_formats():
            raise ValueError(f"Unsupported target format: {target_format}")
        mime_type = ImageFormat.get_mime_type(target_format)

        optimized_image_io = self.processor.optimize_image(pil_image, target_format, quality)
        content = optimized_image_io.getvalue()
        return content, mime_type

    def update_image_metadata(
        self,
        image: Image,
        alt_text: str = None,
        title: str = None,
        description: str = None,
    ):
        if alt_text is not None:
            image.alt_text = alt_text
        if title is not None:
            image.title = title
        if description is not None:
            image.description = description
        image.save()
        return image

    def delete_image(self, image: Image, user):
        if image.uploaded_by != user:
            raise PermissionError("You do not have permission to delete this image.")
        image.delete()
