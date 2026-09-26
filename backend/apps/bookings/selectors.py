"""Lectures liées aux réservations et à la disponibilité (architecture § 3.8)."""
from django.db.models import Exists, IntegerField, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce

from .models import Booking, BookingItem


def _blocking_overlaps(start, end, **target):
    """Lignes actives dont la période [start_date, end_date) chevauche [start, end)."""
    return BookingItem.objects.filter(
        is_blocking=True, start_date__lt=end, end_date__gt=start, **target
    )


def is_booked_between(relation, start, end):
    """
    Expression Exists : la ligne courante (OuterRef) a une réservation active sur
    la période. À utiliser en ~is_booked_between(...) pour filtrer les offres libres.
    """
    return Exists(_blocking_overlaps(start, end, **{relation: OuterRef("pk")}))


def vehicle_is_available(vehicle, start, end):
    return not _blocking_overlaps(start, end, vehicle=vehicle).exists()


def units_taken(relation, start, end):
    """
    Expression : unités déjà réservées (quantité) de la ligne courante (OuterRef)
    sur la période, 0 si aucune. Même estimation prudente que room_units_left.
    """
    overlaps = (
        _blocking_overlaps(start, end, **{relation: OuterRef("pk")})
        .values(relation)
        .annotate(n=Sum("quantity"))
        .values("n")[:1]
    )
    return Coalesce(Subquery(overlaps, output_field=IntegerField()), 0)


def booked_periods(from_date, **target):
    """Périodes déjà réservées (fin exclue), pour le calendrier de disponibilité."""
    return list(
        BookingItem.objects.filter(is_blocking=True, end_date__gt=from_date, **target)
        .order_by("start_date")
        .values_list("start_date", "end_date")
    )


def vehicle_booked_periods(vehicle, from_date):
    return booked_periods(from_date, vehicle=vehicle)


def residence_is_available(residence, start, end):
    return not _blocking_overlaps(start, end, residence=residence).exists()


def room_units_left(room, start, end):
    """
    Chambres encore libres sur la période. Estimation prudente : toutes les
    réservations qui chevauchent la période sont comptées comme simultanées.
    """
    taken = _blocking_overlaps(start, end, room=room).aggregate(n=Sum("quantity"))["n"] or 0
    return max(room.quantity - taken, 0)


def activity_places_left(activity, day):
    """Places restantes pour une activité à une date (None si pas de limite)."""
    if activity.max_participants is None:
        return None
    taken = (
        BookingItem.objects.filter(activity=activity, is_blocking=True, start_date=day)
        .aggregate(n=Sum("quantity"))["n"]
        or 0
    )
    return max(activity.max_participants - taken, 0)


def booking_detail_queryset():
    return Booking.objects.select_related("user", "quote").prefetch_related(
        "items__tour_departure__tour",
        "items__room__hotel",
        "items__residence",
        "items__vehicle",
        "items__activity",
    )


def bookings_for_user(user):
    return booking_detail_queryset().filter(user=user)


def get_booking(reference):
    return booking_detail_queryset().get(reference=reference)
