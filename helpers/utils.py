from PIL import Image
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Model
from django.http.request import HttpRequest
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from ninja import UploadedFile


def send_verification_email(request: HttpRequest, user) -> None:
    """
    Sends verification email to user if the user has a valid email.

    Args:
        request: The request object
        user: The user object
    """
    try:
        token = default_token_generator.make_token(user)
        uid: int = user.id
        scheme = request.scheme
        host = request.get_host()
        url = f"{scheme}://{host}/api/auth/verify_email/{uid}/{token}"

        subject = "Verify your email"
        html_message = render_to_string("email/verify_email.html", {
            "user": user,
            "url": url
        })
        user.send_email(subject=subject, html_message=html_message)
    except Exception as e:
        raise e


def make_slug(model_instance: Model,
              source_field: str,
              slug_field: str = "slug") -> str:
    """
    Creates a unique slug from a source field and checks against a slug field.

    Args:
        model_instance: The model instance to create a slug for
        source_field: The field to generate the slug from (e.g., 'title')
        slug_field: The field to check uniqueness against(e.g., 'slug')

    Returns:
        str: A unique slug.
    """
    base_slug = slugify(getattr(model_instance, source_field))
    unique_slug = base_slug
    while model_instance.__class__.objects.filter(
            **{slug_field: unique_slug}).exists():
        unique_slug = f"{base_slug}-{get_random_string(4)}"
    return unique_slug


def validate_image(image: UploadedFile):
    # Validate file size
    MAX_FILE_SIZE = 5 * 1024 * 1024

    # Allowed image types
    ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif"]
    if image.size > MAX_FILE_SIZE:  # type: ignore
        raise ValueError(
            f"File size exceeds the maximum limit of {
                MAX_FILE_SIZE / (1024*1024)} MB.")

    # Validate file type
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError(
            "Unsupported file type. Only JPEG, PNG, and GIF are allowed.")

    # Validate the file is a valid image
    try:
        with Image.open(image) as img:
            img.verify()  # Verify the image is valid
    except Exception as e:
        raise ValueError(f"Invalid image file: {str(e)}")
