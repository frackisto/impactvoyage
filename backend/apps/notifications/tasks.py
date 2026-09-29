from datetime import timedelta
from smtplib import SMTPException

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone


@shared_task(autoretry_for=(SMTPException, OSError), retry_backoff=30, max_retries=5)
def send_email_task(recipients, subject, text, html=None, reply_to=None):
    """Email multipart : texte brut + HTML (rendu par notifications.emails.render)."""
    message = EmailMultiAlternatives(
        subject, text, settings.DEFAULT_FROM_EMAIL, recipients, reply_to=reply_to or None
    )
    if html:
        message.attach_alternative(html, "text/html")
    message.send()


@shared_task(autoretry_for=(OSError,), retry_backoff=30, max_retries=5)
def send_short_message_task(backend_path, channel, to, text):
    """Message court (WhatsApp, SMS) confié au prestataire configuré."""
    from django.utils.module_loading import import_string

    import_string(backend_path)().send(channel, to, text)


@shared_task
def purge_read_notifications_task():
    """Supprime les notifications lues depuis plus de NOTIFICATION_RETENTION_DAYS jours."""
    from .models import Notification

    limit = timezone.now() - timedelta(days=settings.NOTIFICATION_RETENTION_DAYS)
    deleted, _ = Notification.objects.filter(is_read=True, read_at__lt=limit).delete()
    return deleted
