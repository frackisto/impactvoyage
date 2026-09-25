from .models import TransportService


def transport_list(transport_type=None, origin=None, destination=None, passengers=None):
    qs = TransportService.objects.published()
    if transport_type:
        qs = qs.filter(transport_type=transport_type)
    if origin:
        qs = qs.filter(origin__icontains=origin)
    if destination:
        qs = qs.filter(destination__icontains=destination)
    if passengers:
        qs = qs.exclude(max_passengers__lt=passengers)
    return qs
