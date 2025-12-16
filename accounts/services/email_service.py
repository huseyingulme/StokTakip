from django.conf import settings
from django.core.mail import EmailMultiAlternatives


class EmailService:
    """
    E-posta gönderimlerini tek bir yerde toplayan servis.
    HTML ve plain text gövdeyi birlikte gönderir.
    """

    @staticmethod
    def send_email(subject: str, to_email: str, html_content: str, text_content: str | None = None) -> None:
        """
        Gmail SMTP ile HTML destekli mail gönderir.
        """
        if text_content is None:
            text_content = "Bu mail HTML destekli bir maildir."

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

