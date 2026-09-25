from django.db.models import Count, Prefetch, Q

from apps.accommodations.models import Hotel
from apps.activities.models import Activity
from apps.tours.models import Tour

from .models import Destination


def destination_list(continent=None, featured=None):
    """Destinations publiées avec le nombre de circuits et d'hôtels publiés."""
    qs = Destination.objects.published().annotate(
        tours_count=Count("tours", filter=Q(tours__is_published=True), distinct=True),
        hotels_count=Count("hotels", filter=Q(hotels__is_published=True), distinct=True),
    )
    if continent:
        qs = qs.filter(continent=continent)
    if featured is not None:
        qs = qs.filter(is_featured=featured)
    return qs


def destination_detail(slug):
    """Page détail immersive (CdC § 8) : galerie, tags, circuits, hôtels, activités."""
    return (
        Destination.objects.published()
        .prefetch_related(
            "images",
            "tags",
            Prefetch("tours", queryset=Tour.objects.published().select_related("theme")),
            Prefetch("hotels", queryset=Hotel.objects.published()),
            Prefetch("activities", queryset=Activity.objects.published()),
        )
        .get(slug=slug)
    )
