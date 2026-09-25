from apps.bookings.selectors import is_booked_between

from .models import Vehicle


def vehicle_list(category=None, transmission=None, min_seats=None, max_price=None,
                 available_from=None, available_to=None):
    """Véhicules publiés ; si une période est donnée, seuls les véhicules libres (CdC § 12)."""
    qs = Vehicle.objects.published()
    if category:
        qs = qs.filter(category=category)
    if transmission:
        qs = qs.filter(transmission=transmission)
    if min_seats:
        qs = qs.filter(seats__gte=min_seats)
    if max_price is not None:
        qs = qs.filter(base_price__lte=max_price)
    if available_from and available_to:
        qs = qs.filter(~is_booked_between("vehicle", available_from, available_to))
    return qs


def vehicle_detail(slug):
    return Vehicle.objects.published().prefetch_related("images").get(slug=slug)
