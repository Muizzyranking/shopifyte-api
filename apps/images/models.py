from django.db import models

from core.models import TimestampedModel


class ImageCategory(models.TextChoices):
    UNCATEGORIZED = "uncategorized", "Uncategorized"
    PRODUCTS = "products", "Products"
    LOGO = "logo", "Logo"
    BANNER = "banner", "Banner"


class FileFormat(models.TextChoices):
    JPEG = "jpeg", "JPEG"
    PNG = "png", "PNG"
    WEBP = "webp", "WebP"


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

    format = models.CharField(
        max_length=10,
        choices=FileFormat.choices,
        default=FileFormat.JPEG,
    )

    file_hash = models.CharField(max_length=64, unique=True, db_index=True)

    alt_text = models.CharField(max_length=500, blank=True, null=True)
    uploaded_by = models.ForeignKey(
        "Customer", on_delete=models.SET_NULL, related_name="uploaded_images", blank=True, null=True
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
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["file_hash"]),
            models.Index(fields=["uploaded_by"]),
        ]

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("image_detail", kwargs={"pk": self.pk})
