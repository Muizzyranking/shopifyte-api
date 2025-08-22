from django.db import models
from django.core.files.storage import default_storage

from core.models import TimestampedModel


class ImageCategory(models.TextChoices):
    UNCATEGORIZED = "uncategorized", "Uncategorized"
    PRODUCTS = "products", "Products"
    LOGO = "logo", "Logo"
    BANNER = "banner", "Banner"


class MimeType(models.TextChoices):
    JPEG = "image/jpeg", "JPEG"
    PNG = "image/png", "PNG"
    WEBP = "image/webp", "WebP"
    GIF = "image/gif", "GIF"

    @classmethod
    def get_extension(cls, mime_type):
        mapping = {
            cls.JPEG: "jpg",
            cls.PNG: "png",
            cls.WEBP: "webp",
            cls.GIF: "gif",
        }
        return mapping.get(mime_type, "bin")


class ImageFormat(models.TextChoices):
    JPEG = "jpeg", "JPEG"
    PNG = "png", "PNG"
    WEBP = "webp", "WebP"
    GIF = "gif", "GIF"

    @classmethod
    def get_mime_type(cls, format):
        mapping = {
            cls.JPEG: MimeType.JPEG,
            cls.PNG: MimeType.PNG,
            cls.WEBP: MimeType.WEBP,
            cls.GIF: MimeType.GIF,
        }
        return mapping.get(format, MimeType.JPEG)

    @classmethod
    def get_extension(cls, format):
        return MimeType.get_extension(cls.get_mime_type(format))

    @classmethod
    def supported_transparancy(cls, format_name):
        return format_name in [cls.PNG, cls.JPEG, cls.WEBP, cls.GIF]


class Image(TimestampedModel):
    name = models.CharField(max_length=255)
    category = models.CharField(
        max_length=20,
        choices=ImageCategory.choices,
        default=ImageCategory.UNCATEGORIZED,
        db_index=True,
    )
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)

    file_size = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()

    format = models.CharField(max_length=10, choices=ImageFormat.choices)
    mime_type = models.CharField(max_length=50, choices=MimeType.choices)

    file_hash = models.CharField(max_length=64, unique=True, db_index=True)

    alt_text = models.CharField(max_length=500, blank=True, null=True)
    uploaded_by = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.SET_NULL,
        related_name="uploaded_images",
        blank=True,
        null=True,
    )

    # SEO stuff
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # View count for analytics
    view_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.category} - {self.name}"

    class Meta(TimestampedModel.Meta):
        verbose_name = "Image"
        verbose_name_plural = "Images"
        db_table = "images"
        ordering = ["-created_at"]

    def get_absolute_url(self):
        if self.file_path and default_storage.exists(self.file_path):
            return default_storage.url(self.file_path)

    def delete_file(self):
        if self.file_path and default_storage.exists(self.file_path):
            default_storage.delete(self.file_path)

    def delete(self, *args, **kwargs):
        self.delete_file()
        super().delete(*args, **kwargs)
