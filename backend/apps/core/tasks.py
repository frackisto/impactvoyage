from celery import shared_task

from .services import update_exchange_rates


@shared_task(autoretry_for=(OSError,), retry_backoff=60, max_retries=5)
def update_exchange_rates_task():
    update_exchange_rates()
