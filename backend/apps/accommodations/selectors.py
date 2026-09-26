from math import ceil

from django.db.models import F, OuterRef, Prefetch, Subquery

from apps.bookings.selectors import is_booked_between, units_taken
from apps.reviews.selectors import annotate_ratings

from .models import Amenity, Hotel, Residence, Room


def bookable_rooms(travelers=None, rooms=None, start=None, end=None):
    """
    Types de chambres actifs pouvant loger `travelers` voyageurs répartis dans
    `rooms` chambres (1 par défaut) ; avec une période, il doit rester au moins
    `rooms` chambres libres. units_left = chambres encore libres.
    """
    needed = rooms or 1
    qs = Room.objects.filter(is_active=True)
    if travelers:
        qs = qs.filter(capacity__gte=ceil(travelers / needed))
    taken = units_taken("room", start, end) if start and end else 0
    return qs.annotate(units_left=F("quantity") - taken).filter(units_left__gte=needed)


def hotel_list(destination=None, accommodation_type=None, stars=None, amenities=(),
               min_price=None, max_price=None, travelers=None, rooms=None,
               available_from=None, available_to=None):
    """
    Hébergements publiés (CdC § 7, § 14). price_from = prix de la chambre la moins
    chère qui convient (voyageurs, nombre de chambres, disponibilité sur la
    période) ; avec l'un de ces critères, les hôtels sans chambre adaptée sont exclus.
    """
    cheapest = (
        bookable_rooms(travelers, rooms, available_from, available_to)
        .filter(hotel=OuterRef("pk"))
        .order_by("base_price")
    )
    qs = (
        Hotel.objects.published()
        .select_related("destination")
        .annotate(
            price_from=Subquery(cheapest.values("base_price")[:1]),
            price_from_currency=Subquery(cheapest.values("currency")[:1]),
        )
    )
    if destination:
        qs = qs.filter(destination__slug=destination)
    if accommodation_type:
        qs = qs.filter(accommodation_type=accommodation_type)
    if stars:
        qs = qs.filter(stars=stars)
    for amenity in amenities:
        qs = qs.filter(amenities__pk=amenity)
    if travelers or rooms or available_from:
        qs = qs.filter(price_from__isnull=False)
    if min_price is not None:
        qs = qs.filter(price_from__gte=min_price)
    if max_price is not None:
        qs = qs.filter(price_from__lte=max_price)
    return annotate_ratings(qs)


def room_availability(hotel, start, end):
    """Chambres actives de l'hôtel avec le nombre d'unités libres sur la période."""
    return (
        Room.objects.filter(hotel=hotel, is_active=True)
        .annotate(units_left=F("quantity") - units_taken("room", start, end))
        .order_by("base_price")
    )


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



def amenities_in_use(kind):
    """Équipements d'au moins un hôtel (kind="hotel") ou une résidence publiés, pour les filtres."""
    relation = {"hotel": "hotels", "residence": "residences"}[kind]
    return (
        Amenity.objects.filter(**{f"{relation}__is_published": True})
        .distinct()
        .order_by("name")
    )
