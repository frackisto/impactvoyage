import io
import json
from datetime import date, timedelta
from unittest import mock
from urllib.error import URLError

from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.bookings.models import Booking, BookingItem
from apps.core.tests.admin_helpers import AdminTestCase
from apps.core.tests.helpers import make_booking, make_departure, make_tour, make_user
from apps.dashboard import navigation, selectors, umami
from apps.inquiries.models import ContactMessage, QuoteRequest

UMAMI = {"UMAMI_API_URL": "https://stats.example.com", "UMAMI_WEBSITE_ID": "site-1",
         "UMAMI_API_TOKEN": "secret"}


def book_departure(departure, status=Booking.Status.CONFIRMED, **kwargs):
    booking = make_booking(status=status, **kwargs)
    BookingItem.objects.create(
        booking=booking, tour_departure=departure, label="Circuit", unit_price=1, quantity=1,
        line_total=1, start_date=departure.start_date,
        end_date=departure.end_date + timedelta(days=1))
    return booking


class SelectorTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_month_starts_cross_the_new_year(self):
        starts = selectors.month_starts(date(2026, 2, 17), months=4)
        self.assertEqual(starts, [date(2025, 11, 1), date(2025, 12, 1), date(2026, 1, 1),
                                  date(2026, 2, 1)])

    def test_monthly_counts_include_empty_months(self):
        booking = make_booking()
        two_months_ago = timezone.now() - timedelta(days=62)
        Booking.objects.filter(pk=booking.pk).update(created_at=two_months_ago)
        make_booking()
        starts = selectors.month_starts(timezone.localdate(), months=3)
        counts = selectors.monthly_counts(Booking.objects.all(), starts)
        self.assertEqual(counts[-1], 1)
        self.assertEqual(sum(counts), 2)
        self.assertEqual(len(counts), 3)

    def test_popularity_counts_live_bookings_then_views(self):
        viewed = make_tour(view_count=500)
        booked = make_tour(view_count=3)
        departure = make_departure(tour=booked)
        book_departure(departure)
        book_departure(departure, status=Booking.Status.CANCELLED)  # ne compte pas
        tours = selectors.popular_tours()
        self.assertEqual([t["pk"] for t in tours[:2]], [booked.pk, viewed.pk])
        self.assertEqual(tours[0]["bookings"], 1)
        destinations = selectors.popular_destinations()
        self.assertEqual(destinations[0]["pk"], booked.destination_id)
        self.assertEqual(destinations[0]["bookings"], 1)

    def test_stats_are_cached(self):
        first = selectors.dashboard_stats()
        make_booking(status=Booking.Status.REQUESTED)
        self.assertEqual(selectors.dashboard_stats(), first)
        cache.clear()
        self.assertEqual(selectors.dashboard_stats()["indicators"]["bookings_to_process"], 1)


class DashboardPageTests(AdminTestCase):
    def setUp(self):
        cache.clear()
        make_booking(status=Booking.Status.REQUESTED, contact_name="Awa Koné")
        QuoteRequest.objects.create(first_name="Koffi", last_name="Yao", email="k@example.com",
                                    phone="0102030405", destination_text="Zanzibar")
        ContactMessage.objects.create(name="Ama", email="ama@example.com", subject="Visa",
                                      message="…")

    def labels(self, response):
        return [card["label"] for card in response.context["indicators"]]

    def test_commercial_sees_the_customer_workload(self):
        self.login("COMMERCIAL")
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Devis à traiter", self.labels(response))
        self.assertIn("Réservations à traiter", self.labels(response))
        self.assertContains(response, "Awa Koné")
        self.assertContains(response, "Zanzibar")
        self.assertContains(response, "Demandes de devis par mois")
        self.assertContains(response, "Mesure d'audience non branchée")
        chart = json.loads(response.context["charts"][0]["data"])
        self.assertEqual(len(chart["labels"]), 12)

    def test_agent_does_not_see_customer_data(self):
        self.login("AGENT")
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Réservations à traiter", self.labels(response))
        self.assertIn("Circuits publiés", self.labels(response))
        self.assertNotContains(response, "Awa Koné")
        self.assertEqual(response.context["todo"], [])

    def test_clients_cannot_open_the_backoffice(self):
        self.login("CLIENT")
        response = self.client.get(reverse("admin:index"))
        self.assertRedirects(response, reverse("admin:login") + "?next=" + reverse("admin:index"))


class NavigationTests(TestCase):
    def sidebar(self, role):
        request = RequestFactory().get("/admin/")
        request.user = make_user(role)
        return {group["title"]: [item["title"] for item in group["items"]]
                for group in navigation.sidebar_navigation(request)}

    def test_menu_follows_the_role(self):
        agent = self.sidebar("AGENT")
        self.assertNotIn("Relation client", agent)
        self.assertIn("Circuits", agent["Catalogue"])
        self.assertNotIn("Administration", agent)

        commercial = self.sidebar("COMMERCIAL")
        self.assertEqual(commercial["Relation client"],
                         ["Devis", "Réservations", "Messages", "Avis clients"])
        self.assertIn("Mes notifications", commercial[None])

        admin = self.sidebar("ADMIN")
        self.assertIn("Utilisateurs", admin["Administration"])

    def test_badges_count_pending_work(self):
        request = RequestFactory().get("/admin/")
        request.user = make_user("COMMERCIAL")
        self.assertIsNone(navigation.bookings_to_process(request))
        make_booking(status=Booking.Status.REQUESTED)
        self.assertEqual(navigation.bookings_to_process(request), 1)


class UmamiTests(TestCase):
    def setUp(self):
        cache.clear()

    def response(self, payload):
        return mock.MagicMock(__enter__=lambda s: io.StringIO(json.dumps(payload)),
                              __exit__=lambda *a: False)

    def test_not_configured(self):
        self.assertIsNone(umami.visitor_stats())

    @override_settings(**UMAMI)
    def test_reads_both_payload_formats_and_caches(self):
        old = {"visitors": {"value": 120, "prev": 90}, "pageviews": {"value": 480, "prev": 300}}
        with mock.patch("apps.dashboard.umami.urlopen", return_value=self.response(old)) as call:
            self.assertEqual(umami.visitor_stats(), {"visitors": 120, "pageviews": 480, "days": 30})
            umami.visitor_stats()
        self.assertEqual(call.call_count, 1)
        request = call.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")
        self.assertIn("/api/websites/site-1/stats?startAt=", request.full_url)

        cache.clear()
        new = {"visitors": 7, "pageviews": 9, "visits": 8}
        with mock.patch("apps.dashboard.umami.urlopen", return_value=self.response(new)):
            self.assertEqual(umami.visitor_stats()["visitors"], 7)

    @override_settings(**UMAMI)
    def test_unavailable_umami_does_not_break_the_dashboard(self):
        with mock.patch("apps.dashboard.umami.urlopen", side_effect=URLError("down")):
            self.assertEqual(umami.visitor_stats(), {"unavailable": True})
