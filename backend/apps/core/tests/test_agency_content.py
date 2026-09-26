from django.core.management import call_command
from django.test import TestCase
from django.utils import translation

from apps.accommodations.models import Residence
from apps.core.models import Category, SiteSettings
from apps.destinations.models import Destination
from apps.events.models import Event
from apps.services.models import Service
from apps.vehicles.models import Vehicle
from apps.visas.models import VisaService


class LoadAgencyContentTests(TestCase):
    def test_loads_real_content_idempotently(self):
        call_command("load_agency_content", verbosity=0)
        call_command("load_agency_content", verbosity=0)  # relancer ne crée pas de doublons

        settings = SiteSettings.load()
        self.assertEqual(settings.phone, "+225 27 23 22 88 57")
        self.assertTrue(settings.hero_image)
        self.assertEqual(Category.objects.filter(kind="TOUR_THEME").count(), 7)
        self.assertEqual(Service.objects.count(), 12)
        visa = Service.objects.get(slug="visa-et-formalites")
        self.assertEqual(visa.prices.count(), 7)
        self.assertEqual(VisaService.objects.count(), 6)
        self.assertEqual(
            VisaService.objects.get(destination_country_code="AE").fees, 100000
        )
        dubai = Destination.objects.get(slug="dubai")
        self.assertEqual(dubai.images.count(), 3)
        with translation.override("en"):
            self.assertEqual(Destination.objects.get(slug="chine").name, "China")
        self.assertTrue(Residence.objects.get().is_published)
        # Véhicules incomplets : jamais publiés automatiquement.
        self.assertEqual(Vehicle.objects.count(), 4)
        self.assertFalse(Vehicle.objects.filter(is_published=True).exists())
        self.assertEqual(Event.objects.filter(is_published=True).count(), 1)
