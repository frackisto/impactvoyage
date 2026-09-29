"""
Statistiques du tableau de bord (architecture § 13), mises en cache 5 minutes :
indicateurs, devis et réservations par mois, destinations et circuits
populaires (vues des fiches + réservations). Les listes « à traiter » ne sont
pas mises en cache : elles doivent refléter le travail en cours.
"""
from collections import Counter
from datetime import date

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.accommodations.models import Hotel, Residence
from apps.bookings.models import Booking, BookingItem
from apps.destinations.models import Destination
from apps.inquiries.models import ContactMessage, QuoteRequest
from apps.notifications.models import Notification
from apps.offers.models import Offer
from apps.reviews.models import Review
from apps.tours.models import Tour
from apps.vehicles.models import Vehicle

CACHE_KEY = "dashboard:stats"
MONTHS = 12
TOP = 5

BStatus = Booking.Status
QStatus = QuoteRequest.Status

BOOKINGS_TO_PROCESS = (BStatus.REQUESTED, BStatus.PENDING)
QUOTES_OPEN = (QStatus.NOUVELLE, QStatus.EN_COURS)
# Réservations qui ne comptent pas dans la popularité d'une offre.
LOST_BOOKINGS = (BStatus.CANCELLED, BStatus.REJECTED, BStatus.EXPIRED)

MONTH_LABELS = ("janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.",
                "oct.", "nov.", "déc.")


def month_starts(today, months=MONTHS):
    """Premiers jours des `months` derniers mois, du plus ancien au mois en cours."""
    year, month = today.year, today.month
    starts = []
    for _ in range(months):
        starts.append(date(year, month, 1))
        year, month = (year - 1, 12) if month == 1 else (year, month - 1)
    return starts[::-1]


def monthly_counts(queryset, starts):
    """Nombre d'objets créés chaque mois (0 pour les mois sans activité)."""
    rows = (
        queryset.filter(created_at__date__gte=starts[0])
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Count("pk"))
    )
    by_month = {row["month"].date().replace(day=1): row["total"] for row in rows}
    return [by_month.get(start, 0) for start in starts]


def indicators(today):
    first_of_month = today.replace(day=1)
    return {
        "quotes_open": QuoteRequest.objects.filter(status__in=QUOTES_OPEN).count(),
        "quotes_month": QuoteRequest.objects.filter(created_at__date__gte=first_of_month).count(),
        "bookings_to_process": Booking.objects.filter(status__in=BOOKINGS_TO_PROCESS).count(),
        "bookings_confirmed": Booking.objects.filter(status=BStatus.CONFIRMED).count(),
        "bookings_month": Booking.objects.filter(created_at__date__gte=first_of_month).count(),
        "contacts_unread": ContactMessage.objects.filter(status=ContactMessage.Status.NOUVEAU).count(),
        "reviews_pending": Review.objects.filter(status=Review.Status.EN_ATTENTE).count(),
        "destinations": Destination.objects.published().count(),
        "tours": Tour.objects.published().count(),
        "hotels": Hotel.objects.published().count(),
        "residences": Residence.objects.published().count(),
        "vehicles": Vehicle.objects.published().count(),
        "offers_active": Offer.objects.currently_active().count(),
    }


def _active_items():
    return BookingItem.objects.filter(booking__deleted_at__isnull=True).exclude(
        booking__status__in=LOST_BOOKINGS
    )


def popular_tours(limit=TOP):
    """Circuits les plus réservés, puis les plus consultés."""
    booked = Q(departures__booking_items__booking__deleted_at__isnull=True) & ~Q(
        departures__booking_items__booking__status__in=LOST_BOOKINGS
    )
    tours = (
        Tour.objects.annotate(
            bookings=Count("departures__booking_items__booking", filter=booked, distinct=True)
        )
        .order_by("-bookings", "-view_count", "title")
        .values("pk", "title", "view_count", "bookings")[:limit]
    )
    return list(tours)


def popular_destinations(limit=TOP):
    """Destinations les plus réservées (circuits, hôtels, résidences, activités), puis consultées."""
    paths = ("tour_departure__tour__destination", "room__hotel__destination",
             "residence__destination", "activity__destination")
    bookings = Counter()
    for path in paths:
        rows = (
            _active_items().filter(**{f"{path}__isnull": False})
            .values(path).annotate(total=Count("booking", distinct=True))
        )
        for row in rows:
            bookings[row[path]] += row["total"]
    destinations = [
        {**row, "bookings": bookings.get(row["pk"], 0)}
        for row in Destination.objects.values("pk", "name", "view_count")
    ]
    destinations.sort(key=lambda d: (-d["bookings"], -d["view_count"], d["name"]))
    return destinations[:limit]


def compute_stats(today=None):
    today = today or timezone.localdate()
    starts = month_starts(today)
    return {
        "indicators": indicators(today),
        "months": [f"{MONTH_LABELS[s.month - 1]} {s:%y}" for s in starts],
        "quotes_by_month": monthly_counts(QuoteRequest.objects.all(), starts),
        "bookings_by_month": monthly_counts(Booking.objects.all(), starts),
        "popular_destinations": popular_destinations(),
        "popular_tours": popular_tours(),
        "computed_at": timezone.now(),
    }


def dashboard_stats():
    """Statistiques globales (identiques pour toute l'équipe), en cache 5 minutes."""
    stats = cache.get(CACHE_KEY)
    if stats is None:
        stats = compute_stats()
        cache.set(CACHE_KEY, stats, settings.DASHBOARD_CACHE_SECONDS)
    return stats


# --- Listes « à traiter » (jamais en cache) -----------------------------------


def bookings_to_process(limit=TOP):
    return list(
        Booking.objects.filter(status__in=BOOKINGS_TO_PROCESS)
        .order_by("created_at")[:limit]
    )


def quotes_to_process(limit=TOP):
    return list(
        QuoteRequest.objects.filter(status__in=QUOTES_OPEN)
        .select_related("destination", "assigned_to")
        .order_by("created_at")[:limit]
    )


def unread_notifications(user, limit=TOP):
    return list(Notification.objects.filter(recipient=user, is_read=False)[:limit])
