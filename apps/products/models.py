from django.db import models
from django.utils.text import slugify
from core.models import BaseModel, TimestampedModel


class ProductCategory(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"


class Product(TimestampedModel):
    name = models.CharField(max_length=255)
    shop = models.ForeignKey("shops.Shop", on_delete=models.CASCADE, related_name="products")
    description = models.TextField(blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True)
    stock = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.name} - {self.shop.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = f"{base_slug}-{self.id[:12]}"
            self.slug = slug
        super().save(*args, **kwargs)

    class Meta(TimestampedModel.Meta):
        verbose_name = "Product"
        verbose_name_plural = "Products"


class ProductImages(TimestampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ForeignKey("images.Image", on_delete=models.CASCADE)
    primary = models.BooleanField(default=False)

    class Meta(TimestampedModel.Meta):
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
