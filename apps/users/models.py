import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from core.models import BaseModel


class CustomUser(AbstractUser):
    id = models.UUIDField(unique=True, primary_key=True, editable=False, default=uuid.uuid4)
    email = models.EmailField(unique=True, max_length=255)
    username = models.CharField(max_length=255, unique=True, blank=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    has_store = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.username


class UserAddress(BaseModel):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    street = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    zipcode = models.IntegerField(blank=True)
