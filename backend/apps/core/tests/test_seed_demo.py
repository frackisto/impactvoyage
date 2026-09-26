from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import translation

from apps.accommodations.models import Hotel, Residence
from apps.reviews.models import Review
from apps.tours.models import Tour
from apps.tours.selectors import open_departures


class SeedDemoTests(TestCase):
    def test_loads_demo_tours_idempotently_and_resets(self):
        call_command("seed_demo", verbosity=0)
        call_command("seed_demo", verbosity=0)  # relancer ne crée pas de doublons

        self.assertEqual(Tour.objects.count(), 6)
        self.assertEqual(Tour.objects.filter(scope="NATIONAL").count(), 3)
        dubai = Tour.objects.get(slug="dubai-ville-des-records")
        self.assertEqual(dubai.days.count(), 6)
        self.assertEqual(open_departures().filter(tour=dubai).count(), 3)
        self.assertEqual(dubai.images.count(), 3)
        self.assertTrue(dubai.cover_image)
        with translation.override("en"):
            self.assertEqual(Tour.objects.get(pk=dubai.pk).title, "Dubai, the city of records")
        # Circuit sur mesure : aucun départ programmé.
        self.assertFalse(Tour.objects.get(slug="lune-de-miel-a-dubai").departures.exists())
        self.assertEqual(Review.objects.filter(tour=dubai, status="APPROUVE").count(), 2)

        self.assertEqual(Hotel.objects.count(), 5)
        plateau = Hotel.objects.get(slug="hotel-lagune-plateau")
        self.assertEqual(plateau.rooms.count(), 3)
        self.assertEqual(plateau.amenities.count(), 6)
        self.assertTrue(Hotel.objects.get(slug="marina-view-dubai").images.exists())
        # La résidence réelle de l'agence et la villa de démonstration.
        self.assertEqual(Residence.objects.count(), 2)

        call_command("seed_demo", reset=True, verbosity=0)
        self.assertFalse(Tour.objects.exists())
        self.assertFalse(Hotel.objects.exists())
        self.assertFalse(Review.objects.exists())
        # Le contenu réel de l'agence n'est pas touché.
        self.assertEqual(Residence.objects.count(), 1)

    @override_settings(DEMO_DATA_ALLOWED=False)
    def test_refused_in_production(self):
        with self.assertRaises(CommandError):
            call_command("seed_demo", verbosity=0)
        self.assertFalse(Tour.objects.exists())
