from django.db.models import Min, Prefetch, Q

from apps.bookings.selectors import is_booked_between
from apps.reviews.selectors import annotate_ratings

from .models import Hotel, Residence, Room


def hotel_list(destination=None, accommodation_type=None, stars=None, amenities=(),
               min_price=None, max_price=None, travelers=None):
    """
    Hébergements publiés (CdC § 14). price_from = prix de la chambre active la
    moins chère (pouvant accueillir `travelers` si précisé).
    """
    room_filter = Q(rooms__is_active=True)
    if travelers:
        room_filter &= Q(rooms__capacity__gte=travelers)
    qs = (
        Hotel.objects.published()
        .select_related("destination")
        .annotate(price_from=Min("rooms__base_price", filter=room_filter))
    )
    if destination:
        qs = qs.filter(destination__slug=destination)
    if accommodation_type:
        qs = qs.filter(accommodation_type=accommodation_type)
    if stars:
        qs = qs.filter(stars=stars)
    for amenity in amenities:
        qs = qs.filter(amenities__pk=amenity)
    if travelers:
        qs = qs.filter(price_from__isnull=False)
    if min_price is not None:
        qs = qs.filter(price_from__gte=min_price)
    if max_price is not None:
        qs = qs.filter(price_from__lte=max_price)
    return annotate_ratings(qs)


def hotel_detail(slug):
    return (
        Hotel.objects.published()
        .select_related("destination")
        .prefetch_related(
            "images",
            "amenities",
            Prefetch("rooms", queryset=Room.objects.filter(is_active=True)),
        )
        .get(slug=slug)
    )


def residence_list(destination=None, min_capacity=None, min_rooms=None, amenities=(),
                   min_price=None, max_price=None, available_from=None, available_to=None):
    qs = Residence.objects.published().select_related("destination")
    if destination:
        qs = qs.filter(destination__slug=destination)
    if min_capacity:
        qs = qs.filter(capacity__gte=min_capacity)
    if min_rooms:
        qs = qs.filter(rooms_count__gte=min_rooms)
    for amenity in amenities:
        qs = qs.filter(amenities__pk=amenity)
    if min_price is not None:
        qs = qs.filter(base_price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(base_price__lte=max_price)
    if available_from and available_to:
        qs = qs.filter(~is_booked_between("residence", available_from, available_to))
    return qs


def residence_detail(slug):
    return (
        Residence.objects.published()
        .select_related("destination")
        .prefetch_related("images", "amenities")
        .get(slug=slug)
    )

