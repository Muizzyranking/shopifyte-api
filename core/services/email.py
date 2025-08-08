from dataclasses import dataclass
from enum import Enum
from typing import Any

from django.conf import settings
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives


class EmailType(Enum):
    CONFIRMATION = "confirmation"


@dataclass
class EmailTypeSchema:
    description: str
    context: list[str]
    template_dir: str


class EmailConfig:
    """
    Email configuration class that holds the schemas for different email types.
    """

    EMAIL_SCHEMAS = {
        EmailType.CONFIRMATION: EmailTypeSchema(
            description="Confirmation email",
            context=["name", "confirmation_url"],
            template_dir="emails/confirmation",
        )
    }

    @classmethod
    def get_templates(cls, email_type: EmailType):
        """
        Get the email template schema for a given email type.
        """
        email_schema = cls.EMAIL_SCHEMAS.get(email_type, None)
        if email_schema is None:
            raise ValueError(f"Email type {email_type} is not supported.")
        template_dir = email_schema.template_dir
        return {
            "subject": f"{template_dir}/subject.txt",
            "text_template": f"{template_dir}/body.txt",
            "html_template": f"{template_dir}/body.html",
        }

    @classmethod
    def validate_context(cls, email_type: EmailType, context: dict[str, Any]):
        """
        Validate the context against the expected schema for the given email type.
        """
        email_schema = cls.EMAIL_SCHEMAS.get(email_type, None)
        if email_schema is None:
            raise ValueError(f"Email type {email_type} is not supported.")

        missing_keys = [key for key in email_schema.context if key not in context]
        if missing_keys:
            raise ValueError(f"Missing keys in context: {', '.join(missing_keys)}")

        return True


class EmailService:
    def __init__(self, from_email: str | None = None):
        self.from_email = getattr(settings, "DEFAULT_FROM_EMAIL", from_email)
        if not self.from_email:
            raise ValueError("Default from email is not set in settings.")

    @staticmethod
    def render_template(template_path: str, context: dict[str, Any]):
        try:
            return render_to_string(template_path, context)
        except TemplateDoesNotExist:
            raise ValueError(f"Template {template_path} does not exist.")
        except Exception as e:
            raise ValueError(f"Error rendering template {template_path}: {str(e)}")

    def send_email(
        self,
        email_type: EmailType,
        to_emails: list[str],
        context: dict[str, Any],
        fail_silently: bool = False,
    ):
        try:
            EmailConfig.validate_context(email_type, context)
            templates = EmailConfig.get_templates(email_type)
            subject = self.render_template(templates["subject"], context).strip()
            text_body = self.render_template(templates["text_template"], context)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=self.from_email,
                to=to_emails,
            )
            try:
                html_body = self.render_template(templates["html_template"], context)
                email.attach_alternative(html_body, "text/html")
            except TemplateDoesNotExist:
                pass
            except Exception as e:
                if not fail_silently:
                    raise ValueError(f"Error rendering HTML template: {str(e)}")

            email.send(fail_silently=fail_silently)
            return True
        except Exception:
            pass

    def send_confirmation_email(self, user):
        context = {"name": user.get_full_name(), "confirmation_url": ""}
        return self.send_email(
            email_type=EmailType.CONFIRMATION,
            to_emails=[user.email],
            context=context,
        )
