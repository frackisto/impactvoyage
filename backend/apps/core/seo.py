"""
Contenus publics du plan du site (Phase 21, architecture § 9) : tout ce qu'un
moteur de recherche peut indexer, avec la date de dernière modification. Le
frontend construit sitemap.xml à partir de cette liste (une URL par langue).
"""
from django.db.models import Max

from apps.accommodations.models import Hotel, Residence
from apps.activities.models import Activity
from apps.blog.models import BlogPost
from apps.destinations.models import Destination
from apps.events.models import Event
from apps.media.models import MediaAlbum
from apps.offers.models import Offer
from apps.tours.models import Tour
from apps.vehicles.models import Vehicle
from apps.visas.models import VisaService


def _entries(queryset):
    return [{"slug": slug, "updated_at": updated}
            for slug, updated in queryset.order_by("slug").values_list("slug", "updated_at")]


def sitemap_entries():
    """{type de contenu: [{slug, updated_at}]}, contenus publiés uniquement."""
    visa_countries = (
        VisaService.objects.published().values("country_slug")
        .annotate(updated_at=Max("updated_at")).order_by("country_slug")
    )
    return {
        "destinations": _entries(Destination.objects.published()),
        "tours": _entries(Tour.objects.published()),
        "hotels": _entries(Hotel.objects.published()),
        "residences": _entries(Residence.objects.published()),
        "vehicles": _entries(Vehicle.objects.published()),
        "activities": _entries(Activity.objects.published()),
        "events": _entries(Event.objects.published()),
        "offers": _entries(Offer.objects.currently_active()),
        "blog": _entries(BlogPost.objects.published()),
        "albums": _entries(MediaAlbum.objects.published()),
        "visas": [{"slug": row["country_slug"], "updated_at": row["updated_at"]}
                  for row in visa_countries],
    }
