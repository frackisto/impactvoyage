from django.db.models import Exists, F, Min, OuterRef, Prefetch, Q
from django.utils import timezone

from apps.activities.models import Activity
from apps.reviews.selectors import annotate_ratings

from .models import Tour, TourDeparture


def open_departures():
    """Départs réservables : ouverts, à venir, avec au moins une place."""
    return TourDeparture.objects.filter(
        status=TourDeparture.Status.OPEN,
        start_date__gte=timezone.localdate(),
        seats_reserved__lt=F("capacity"),
    )


def _open_departure_q():
    return Q(
        departures__status=TourDeparture.Status.OPEN,
        departures__start_date__gte=timezone.localdate(),
        departures__seats_reserved__lt=F("departures__capacity"),
    )


def tour_list(scope=None, theme=None, destination=None, continent=None, country_code=None,
              min_price=None, max_price=None, max_days=None, departure_from=None,
              departure_to=None, travelers=None):
    """
    Circuits publiés filtrés selon le moteur de recherche (CdC § 7, § 10).
    Les filtres de date et de nombre de voyageurs portent sur les départs ouverts ;
    next_departure = prochain départ ouvert.
    """
    qs = Tour.objects.published().select_related("destination", "theme")
    if scope:
        qs = qs.filter(scope=scope)
    if theme:
        qs = qs.filter(theme__slug=theme)
    if destination:
        qs = qs.filter(destination__slug=destination)
    if continent:
        qs = qs.filter(destination__continent=continent)
    if country_code:
        qs = qs.filter(destination__country_code=country_code)
    if min_price is not None:
        qs = qs.filter(base_price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(base_price__lte=max_price)
    if max_days:
        qs = qs.filter(duration_days__lte=max_days)

    if departure_from or departure_to or travelers:
        departures = open_departures().filter(tour=OuterRef("pk"))
        if departure_from:
            departures = departures.filter(start_date__gte=departure_from)
        if departure_to:
            departures = departures.filter(start_date__lte=departure_to)
        if travelers:
            departures = departures.filter(capacity__gte=F("seats_reserved") + travelers)
        qs = qs.filter(Exists(departures))

    qs = qs.annotate(next_departure=Min("departures__start_date", filter=_open_departure_q()))
    return annotate_ratings(qs)


def tour_detail(slug):
    """Page circuit : galerie, programme, départs ouverts, activités incluses."""
    return (
        Tour.objects.published()
        .select_related("destination", "theme")
        .prefetch_related(
            "images",
            "days",
            Prefetch("departures", queryset=open_departures(), to_attr="open_departures"),
            Prefetch("activities", queryset=Activity.objects.published()),
        )
        .get(slug=slug)
    )
