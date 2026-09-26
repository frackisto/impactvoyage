from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.bookings.models import BookingItem
from apps.core.tests.helpers import make_activity, make_booking
from apps.core.tests.test_api import API, ApiTestCase


def in_days(n):
    return timezone.localdate() + timedelta(days=n)


def register(activity, day, quantity):
    """Inscription confirmée (bloquante) de `quantity` participants."""
    return BookingItem.objects.create(
        booking=make_booking(), activity=activity, label="Test", unit_price=Decimal("1"),
        line_total=Decimal("1"), quantity=quantity, start_date=day, end_date=day + timedelta(days=1),
        is_blocking=True,
    )


class ActivityDateTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.small = make_activity(max_participants=10)
        self.open = make_activity(max_participants=None)
        register(self.small, in_days(10), 8)

    def slugs(self, **params):
        return {a["slug"]: a["places_left"] for a in self.client.get(f"{API}/activities/", params).data["results"]}

    def test_date_filter_keeps_activities_with_enough_places(self):
        self.assertEqual(self.slugs(), {self.small.slug: None, self.open.slug: None})
        self.assertEqual(self.slugs(date=in_days(10)), {self.small.slug: 2, self.open.slug: None})
        self.assertEqual(self.slugs(date=in_days(10), participants=3), {self.open.slug: None})
        self.assertEqual(self.slugs(date=in_days(11)), {self.small.slug: 10, self.open.slug: None})

    def test_availability(self):
        url = f"{API}/activities/{self.small.slug}/availability/"
        self.assertEqual(
            self.client.get(url, {"date": in_days(10), "participants": 3}).json(),
            {"date": str(in_days(10)), "places_left": 2, "available": False},
        )
        self.assertTrue(self.client.get(url, {"date": in_days(10), "participants": 2}).json()["available"])
        unlimited = self.client.get(f"{API}/activities/{self.open.slug}/availability/", {"date": in_days(10)}).json()
        self.assertEqual(unlimited["places_left"], None)
        self.assertTrue(unlimited["available"])
        self.assertEqual(self.client.get(url).status_code, 400)

    def test_detail_has_no_places_left(self):
        self.assertNotIn("places_left", self.client.get(f"{API}/activities/{self.small.slug}/").data)
