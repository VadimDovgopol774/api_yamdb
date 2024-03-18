from django.core.mail import send_mail
from django.conf import settings


def send_email_to_user(email, code):
    """Отправляет письмо с кодом подтверждения регистрации на YaMDB."""
    send_mail(
        subject='Подтвердите вашу регистрацию на YaMDB',
        message=f'Ваш код подтверждения: {code}',
        from_email=settings.EMAIL_FROM,
        recipient_list=[email],
        fail_silently=True,
    )
