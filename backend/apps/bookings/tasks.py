from celery import shared_task

from . import services


@shared_task
def expire_pending_bookings_task():
    return services.expire_pending_bookings()


@shared_task
def complete_past_bookings_task():
    return services.complete_past_bookings()
