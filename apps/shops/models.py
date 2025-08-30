from django.db import models
from core.models import BaseModel, TimestampedModel
from django.utils.text import slugify

COMMISSION_RATE = 5.0  # Default commission rate percentage


class ShopCategory(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class ShopStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    SUSPENDED = "suspended", "Suspended"


class Shop(TimestampedModel):
    owner = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE, related_name="shops")
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    description = models.TextField(blank=True, null=True)

    email = models.EmailField(blank=True, null=True)

    # address
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    status = models.CharField(choices=ShopStatus.choices, default=ShopStatus.ACTIVE, max_length=20)

    class Meta(TimestampedModel.Meta):
        ordering = ["-created_at"]
        db_table = "Shops"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["owner"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Shop.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status == ShopStatus.ACTIVE

    def get_url(self):
        return f"/shops/{self.slug}"


class ShopProfile(TimestampedModel):
    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name="profile")

    phone = models.CharField(max_length=20, blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)

    address_line = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    logo = models.ForeignKey(
        "images.Image", on_delete=models.SET_NULL, null=True, blank=True, related_name="shop_logos"
    )

    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    website = models.URLField(blank=True, null=True)

    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(max_length=160, blank=True)

    # Settings
    is_featured = models.BooleanField(default=False)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=COMMISSION_RATE)

    class Meta(TimestampedModel.Meta):
        db_table = "ShopProfiles"

    def __str__(self):
        return f"Profile of {self.shop.name}"
