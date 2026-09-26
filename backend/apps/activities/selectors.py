from django.db.models import F, Q

from apps.bookings.selectors import places_taken_on

from .models import Activity


def activity_list(destination=None, category=None, max_price=None, max_hours=None,
                  date=None, participants=None):
    """
    Activités publiées (CdC § 7). Avec une date : seules celles qui ont encore
    `participants` places (1 par défaut) ce jour-là, avec places_left (None = sans limite).
    """
    qs = Activity.objects.published().select_related("destination", "category")
    if destination:
        qs = qs.filter(destination__slug=destination)
    if category:
        qs = qs.filter(category__slug=category)
    if max_price is not None:
        qs = qs.filter(base_price__lte=max_price)
    if max_hours:
        qs = qs.filter(duration_hours__lte=max_hours)
    if date:
        qs = qs.annotate(places_left=F("max_participants") - places_taken_on(date)).filter(
            Q(max_participants__isnull=True) | Q(places_left__gte=participants or 1)
        )
    return qs


def activity_detail(slug):
    return (
        Activity.objects.published()
        .select_related("destination", "category")
        .prefetch_related("images")
        .get(slug=slug)
    )
