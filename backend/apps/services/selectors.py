from .models import Service


def service_list():
    return Service.objects.published().prefetch_related("prices")
