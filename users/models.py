from config import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from django.core.mail import send_mail


class User(AbstractUser):
    email = models.EmailField(unique=True, max_length=255)
    username = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    has_store = models.BooleanField(default=False)
    street = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    zipcode = models.IntegerField(blank=True)
    phone_number = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"

    def send_email(self, subject, message=None, html_message=None):
        """
        User method to send mail to a user

        Args:
            subject - the subject of the email
            message - the message to be sent
        """
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            html_message=html_message
        )


class Store(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    store_slug = models.SlugField(unique=True, blank=True)
    store_name = models.CharField(max_length=255)
    store_desc = models.TextField(unique=True)
    store_street = models.CharField(max_length=255)
    store_city = models.CharField(max_length=255)
    store_country = models.CharField(max_length=255)
    store_zipcode = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.store_name} - {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.store_slug:
            base_slug = slugify(self.store_name)
            unique_slug = base_slug
            while Store.objects.filter(store_slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{get_random_string(4)}"
            self.store_slug = unique_slug
        super().save(*args, **kwargs)
