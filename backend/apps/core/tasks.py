from celery import shared_task

from .privacy import apply_retention
from .services import update_exchange_rates


@shared_task(autoretry_for=(OSError,), retry_backoff=60, max_retries=5)
def update_exchange_rates_task():
    update_exchange_rates()


@shared_task
def apply_retention_task():
    """Durées de conservation des données personnelles (PERSONAL_DATA_RETENTION_DAYS)."""
    return apply_retention()
