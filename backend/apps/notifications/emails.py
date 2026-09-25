"""
Envoi d'emails asynchrone. Les contenus sont en texte brut ; les gabarits HTML
et traduits arrivent en Phase 20 (Notifications).
"""
from django.db import transaction


def send_email(to, subject, body):
    """Programme l'envoi après validation de la transaction (jamais d'email pour un rollback)."""
    from .tasks import send_email_task

    recipients = [to] if isinstance(to, str) else list(to)
    transaction.on_commit(lambda: send_email_task.delay(recipients, subject, body))
