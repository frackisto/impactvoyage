from datetime import timedelta
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone, translation

from apps.accommodations.models import Hotel, Residence
from apps.activities.models import Activity
from apps.blog.models import BlogPost
from apps.bookings.models import Booking
from apps.bookings.selectors import activity_places_left, vehicle_is_available
from apps.bookings.services import get_booking_for_client
from apps.core.models import Tag
from apps.events.models import Event
from apps.inquiries.models import QuoteRequest
from apps.inquiries.services import accept_quote, get_quote_for_client
from apps.media.models import MediaAlbum
from apps.offers.models import Offer
from apps.reviews.models import Review
from apps.tours.models import Tour
from apps.tours.selectors import open_departures
from apps.transport.models import TransportService
from apps.vehicles.models import Vehicle


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

        # 6 véhicules publiés ; les 4 véhicules réels, incomplets, restent non publiés.
        self.assertEqual(Vehicle.objects.filter(is_published=True).count(), 6)
        vitara = Vehicle.objects.get(slug="demo-suzuki-vitara")
        start = timezone.localdate() + timedelta(days=6)
        self.assertFalse(vehicle_is_available(vitara, start, start + timedelta(days=1)))
        self.assertEqual(Booking.objects.count(), 3)  # recréées, pas dupliquées (hors devis)
        # Demande de réservation fictive : suivie par son lien, elle ne bloque pas la villa.
        demo_booking = get_booking_for_client("IV-DEMO-000001", "7e57d3a0-0000-4000-8000-000000000101")
        self.assertEqual(demo_booking.status, "REQUESTED")
        self.assertFalse(demo_booking.items.get().is_blocking)

        # Activités : 18 inscrits sur 20 dans 10 jours ; 3 activités incluses dans le circuit Dubaï.
        self.assertEqual(Activity.objects.count(), 6)
        visit = Activity.objects.get(slug="visite-guidee-grand-bassam")
        self.assertEqual(activity_places_left(visit, timezone.localdate() + timedelta(days=10)), 2)
        self.assertEqual(dubai.activities.count(), 3)
        # Événements : celui publié par l'agence et deux de démonstration.
        self.assertEqual(Event.objects.filter(is_published=True).count(), 3)
        self.assertEqual(Event.objects.get(slug="voyage-de-groupe-dubai-2026").media.count(), 2)

        # Devis fictifs : consultables et acceptables par leur lien, recréés sans doublon.
        self.assertEqual(QuoteRequest.objects.count(), 2)
        quote = get_quote_for_client("DV-DEMO-000001", "7e57d3a0-0000-4000-8000-000000000001")
        self.assertEqual(quote.status, "DEVIS_ENVOYE")
        accept_quote("DV-DEMO-000001", "7e57d3a0-0000-4000-8000-000000000001")
        call_command("seed_demo", verbosity=0)  # la démonstration revient à son état initial
        self.assertEqual(QuoteRequest.objects.get(reference="DV-DEMO-000001").status, "DEVIS_ENVOYE")

        # Offres en cours (dont une sur le week-end à Mondoukou), transports, albums, articles.
        self.assertEqual(Offer.objects.currently_active().count(), 3)
        self.assertEqual(Offer.objects.get(slug="week-end-mondoukou-prix-doux").tour.slug,
                         "week-end-balneaire-mondoukou")
        self.assertEqual(TransportService.objects.filter(is_published=True).count(), 4)
        self.assertEqual(MediaAlbum.objects.get(slug="dubai-en-images").items.count(), 4)
        self.assertEqual(BlogPost.objects.published().count(), 3)
        self.assertEqual(BlogPost.objects.get(slug="valise-pour-dubai").tags.count(), 1)

        call_command("seed_demo", reset=True, verbosity=0)
        self.assertFalse(Offer.objects.exists())
        self.assertFalse(TransportService.objects.exists())
        self.assertFalse(MediaAlbum.objects.exists())
        self.assertFalse(BlogPost.objects.exists())
        self.assertFalse(Tag.objects.exists())
        self.assertFalse(Tour.objects.exists())
        self.assertFalse(Hotel.objects.exists())
        self.assertFalse(Review.objects.exists())
        self.assertFalse(Booking.objects.exists())
        self.assertFalse(QuoteRequest.all_objects.exists())
        # Le contenu réel de l'agence n'est pas touché.
        self.assertEqual(Residence.objects.count(), 1)
        self.assertEqual(Vehicle.objects.count(), 4)
        self.assertFalse(Activity.objects.exists())
        self.assertEqual(Event.objects.count(), 2)  # les deux événements réels de l'agence

    def test_reload_another_day_replaces_departures(self):
        last_week = timezone.localdate() - timedelta(days=7)
        with mock.patch("django.utils.timezone.localdate", return_value=last_week):
            call_command("seed_demo", verbosity=0)
        call_command("seed_demo", verbosity=0)
        dubai = Tour.objects.get(slug="dubai-ville-des-records")
        self.assertEqual(dubai.departures.count(), 3)
        self.assertFalse(dubai.departures.filter(start_date__lt=timezone.localdate()).exists())

    @override_settings(DEMO_DATA_ALLOWED=False)
    def test_refused_in_production(self):
        with self.assertRaises(CommandError):
            call_command("seed_demo", verbosity=0)
        self.assertFalse(Tour.objects.exists())
