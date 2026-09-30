from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.core.cache import cache
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.core.models import ExchangeRate, SiteSettings
from apps.core.tests.factories import (
    DestinationFactory,
    TourDepartureFactory,
    TourFactory,
    VehicleFactory,
)
from apps.visas.models import VisaService

API = "/api/v1"


def in_days(n):
    return timezone.localdate() + timedelta(days=n)


class ApiTestCase(APITestCase):
    """Cache vidé à chaque test : compteurs de débit et taux de change indépendants."""

    def setUp(self):
        cache.clear()


class CatalogApiTests(ApiTestCase):
    def test_tour_list_is_paginated_filtered_searched_and_sorted(self):
        cheap = TourDepartureFactory(start_date=in_days(20), end_date=in_days(22), capacity=3)
        cheap.tour.base_price = Decimal("90000")
        cheap.tour.title_fr = "Plages d'Assinie"
        cheap.tour.save()
        TourDepartureFactory(start_date=in_days(40), end_date=in_days(42), capacity=20)

        response = self.client.get(f"{API}/tours/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {"count", "next", "previous", "results"})
        self.assertEqual(response.data["count"], 2)

        self.assertEqual(self.client.get(f"{API}/tours/?travelers=5").data["count"], 1)
        self.assertEqual(self.client.get(f"{API}/tours/?search=assinie").data["count"], 1)
        ordered = self.client.get(f"{API}/tours/?ordering=base_price").data["results"]
        self.assertEqual(ordered[0]["slug"], cheap.tour.slug)

    def test_invalid_filter_uses_the_error_format(self):
        response = self.client.get(f"{API}/tours/?travelers=0&scope=LUNE")
        self.assertEqual(response.status_code, 400)
        error = response.data["error"]
        self.assertEqual(error["code"], "validation_error")
        self.assertEqual(set(error["details"]), {"travelers", "scope"})

    def test_page_size_is_capped(self):
        for _ in range(3):
            TourFactory()
        response = self.client.get(f"{API}/tours/?page_size=1000")
        self.assertEqual(len(response.data["results"]), 3)
        self.assertEqual(self.client.get(f"{API}/tours/?page_size=2").data["next"] is not None,
                         True)

    def test_detail_by_slug_and_unpublished_is_404(self):
        departure = TourDepartureFactory(start_date=in_days(20), end_date=in_days(22))
        response = self.client.get(f"{API}/tours/{departure.tour.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["departures"]), 1)
        departures = self.client.get(f"{API}/tours/{departure.tour.slug}/departures/")
        self.assertEqual(departures.data[0]["seats_left"], 10)

        hidden = TourFactory(is_published=False)
        response = self.client.get(f"{API}/tours/{hidden.slug}/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error"]["code"], "not_found")

    def test_language_and_currency(self):
        destination = DestinationFactory(name_fr="Côte d'Ivoire", name_en="Ivory Coast")
        ExchangeRate.objects.create(currency="EUR", rate_from_xof=Decimal("0.0015244902"))
        TourFactory(destination=destination)

        en = self.client.get(f"{API}/destinations/{destination.slug}/", HTTP_ACCEPT_LANGUAGE="en")
        self.assertEqual(en.data["name"], "Ivory Coast")
        fr = self.client.get(f"{API}/destinations/{destination.slug}/?lang=fr",
                             HTTP_ACCEPT_LANGUAGE="en")
        self.assertEqual(fr.data["name"], "Côte d'Ivoire")

        tours = self.client.get(f"{API}/tours/", HTTP_X_CURRENCY="EUR").data["results"]
        self.assertEqual(tours[0]["price"]["display"], {"amount": "228.67", "currency": "EUR"})

    def test_vehicle_availability(self):
        vehicle = VehicleFactory()
        url = f"{API}/vehicles/{vehicle.slug}/availability/"
        response = self.client.get(url, {"start": in_days(3), "end": in_days(5)})
        self.assertEqual(response.data, {"available": True, "booked_periods": []})
        self.assertEqual(self.client.get(url, {"start": in_days(5), "end": in_days(3)})
                         .status_code, 400)

    def test_visas_by_country(self):
        VisaService.objects.create(
            destination_country_code="FR", country_slug="france", nationality_code="CI",
            visa_type="Court séjour", purpose=VisaService.Purpose.TOURISME,
            required_documents="Passeport\nPhotos",
        )
        response = self.client.get(f"{API}/visas/france/")
        self.assertEqual(response.data[0]["required_documents"], ["Passeport", "Photos"])
        self.assertEqual(self.client.get(f"{API}/visas/?nationality_code=sn").data["count"], 0)
        self.assertEqual(self.client.get(f"{API}/visas/espagne/").status_code, 404)

    def test_site_settings_currencies_and_health(self):
        SiteSettings.objects.create(agency_name="Impact Voyage", phone="+225 27 00 00 00")
        self.assertEqual(self.client.get(f"{API}/site-settings/").data["phone"],
                         "+225 27 00 00 00")
        self.assertEqual(self.client.get(f"{API}/currencies/").status_code, 200)
        self.assertEqual(self.client.get(f"{API}/health/").data["status"], "ok")

    def test_catalog_is_read_only(self):
        self.assertEqual(self.client.post(f"{API}/tours/", {}).status_code, 405)

    def test_contact_message_keeps_the_page_language(self):
        from apps.inquiries.models import ContactMessage

        payload = {"name": "Yao", "email": "yao@example.com", "subject": "Info",
                   "message": "Hello, I would like some information."}
        response = self.client.post(f"{API}/contact/", payload, HTTP_ACCEPT_LANGUAGE="en")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ContactMessage.objects.get().language, "en")


class ThrottleTests(ApiTestCase):
    def test_contact_form_is_rate_limited(self):
        """Quota réel du formulaire de contact : 5 envois par heure et par IP."""
        payload = {"name": "Yao", "email": "yao@example.com", "subject": "Info",
                   "message": "Bonjour, je voudrais des informations."}
        for _ in range(5):
            self.assertEqual(self.client.post(f"{API}/contact/", payload).status_code, 201)
        response = self.client.post(f"{API}/contact/", payload)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.data["error"]["code"], "throttled")
        self.assertIn("wait", response.data["error"]["details"])


class OpenApiSchemaTests(ApiTestCase):
    def test_schema_generates_without_warnings(self):
        call_command("spectacular", "--validate", "--fail-on-warn", stdout=StringIO())
        self.assertEqual(self.client.get(f"{API}/schema/").status_code, 200)
