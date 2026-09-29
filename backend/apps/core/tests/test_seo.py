import json
from datetime import timedelta
from decimal import Decimal
from unittest import mock
from urllib.error import URLError

from django.db import transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.core import revalidation
from apps.core.tests.admin_helpers import AdminTestCase
from apps.core.tests.helpers import make_departure, make_destination, make_tour
from apps.offers.models import Offer
from apps.tours.models import Tour
from apps.visas.models import VisaService

from .test_api import API, ApiTestCase

REVALIDATE = {"FRONTEND_REVALIDATE_URL": "http://frontend:3000/api/revalidate",
              "FRONTEND_SHARED_SECRET": "secret-partage"}


class SitemapApiTests(ApiTestCase):
    def test_lists_only_published_content(self):
        tour = make_tour(slug="dubai")
        make_tour(slug="brouillon", is_published=False)
        today = timezone.localdate()
        Offer.objects.create(title="Promo", slug="promo", offer_type="CIRCUIT",
                             initial_price=Decimal("100"), promo_price=Decimal("80"),
                             start_date=today, end_date=today + timedelta(days=5))
        Offer.objects.create(title="Finie", slug="finie", offer_type="CIRCUIT",
                             initial_price=Decimal("100"), promo_price=Decimal("80"),
                             start_date=today - timedelta(days=9), end_date=today - timedelta(days=1))
        for purpose in ("TOURISME", "AFFAIRES"):
            VisaService.objects.create(destination_country_code="FR", country_slug="france",
                                       nationality_code="CI", visa_type="Schengen",
                                       purpose=purpose)

        data = self.client.get(f"{API}/seo/sitemap/").data
        self.assertEqual([e["slug"] for e in data["tours"]], ["dubai"])
        self.assertEqual(data["tours"][0]["updated_at"], tour.updated_at)
        self.assertEqual([e["slug"] for e in data["offers"]], ["promo"])
        self.assertEqual([e["slug"] for e in data["visas"]], ["france"])  # un pays, une page
        self.assertIn(tour.destination.slug, [e["slug"] for e in data["destinations"]])
        self.assertEqual(set(data), {"destinations", "tours", "hotels", "residences", "vehicles",
                                     "activities", "events", "offers", "blog", "albums", "visas"})


@override_settings(**REVALIDATE)
class RevalidationTests(TestCase):
    def setUp(self):
        revalidation._pending.tags = None

    def committed_tags(self, action):
        # Un TestCase ne valide jamais sa transaction : on oublie les étiquettes des
        # objets préparés avant l'action observée.
        revalidation._pending.tags = None
        with mock.patch.object(revalidation.revalidate_frontend_task, "delay") as delay, \
             self.captureOnCommitCallbacks(execute=True):
            action()
        return [set(call.args[0]) for call in delay.call_args_list]

    def test_saving_content_revalidates_its_pages_once_per_transaction(self):
        destination = make_destination()

        def edit():
            tour = make_tour(destination=destination)
            tour.title = "Nouveau titre"
            tour.save()
            make_departure(tour=tour)

        calls = self.committed_tags(edit)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], {"tours", "offers", "sitemap"})

    def test_many_to_many_and_deletion(self):
        tour = make_tour()
        self.assertIn({"tours", "offers", "sitemap"},
                      self.committed_tags(lambda: tour.activities.clear()))
        self.assertIn({"tours", "offers", "sitemap"}, self.committed_tags(tour.delete))

    def test_rolled_back_transaction_does_not_block_later_revalidations(self):
        tour = make_tour()
        with mock.patch.object(revalidation.revalidate_frontend_task, "delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                try:
                    with transaction.atomic():
                        tour.save()
                        raise RuntimeError
                except RuntimeError:
                    pass
            self.assertFalse(delay.called)
            with self.captureOnCommitCallbacks(execute=True):
                tour.save()
            self.assertTrue(delay.called)

    @override_settings(FRONTEND_REVALIDATE_URL="")
    def test_disabled_without_url(self):
        self.assertEqual(self.committed_tags(make_tour), [])

    def test_task_calls_the_site_with_the_shared_secret(self):
        response = mock.MagicMock(status=200)
        response.__enter__.return_value = response
        with mock.patch("apps.core.revalidation.urlopen", return_value=response) as call:
            revalidation.revalidate_frontend_task.run(["tours", "sitemap"])
        request = call.call_args.args[0]
        self.assertEqual(request.full_url, "http://frontend:3000/api/revalidate")
        self.assertEqual(request.get_header("X-frontend-secret"), "secret-partage")
        self.assertEqual(json.loads(request.data), {"tags": ["tours", "sitemap"]})

    def test_unreachable_site_is_retried(self):
        with mock.patch("apps.core.revalidation.urlopen", side_effect=URLError("down")), \
             self.assertRaises(URLError):
            revalidation.revalidate_frontend_task.run(["tours"])
        self.assertIn(URLError, revalidation.revalidate_frontend_task.autoretry_for)


@override_settings(**REVALIDATE)
class AdminBulkActionsTests(AdminTestCase):
    def test_bulk_publication_revalidates_although_update_sends_no_signal(self):
        revalidation._pending.tags = None
        tour = make_tour(is_published=False)
        self.login("AGENT")
        with mock.patch.object(revalidation.revalidate_frontend_task, "delay") as delay, \
             self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("admin:tours_tour_changelist"),
                             {"action": "publish", "_selected_action": [tour.pk]})
        self.assertTrue(Tour.objects.get(pk=tour.pk).is_published)
        self.assertIn("tours", delay.call_args.args[0])
