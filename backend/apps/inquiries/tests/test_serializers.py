from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.accounts.serializers import RegisterSerializer
from apps.bookings.serializers import BookingRequestSerializer
from apps.bookings.services import ItemRequest
from apps.core.tests.helpers import make_destination, make_tour, make_user
from apps.inquiries.serializers import QuoteRequestCreateSerializer
from apps.reviews.serializers import ReviewCreateSerializer


def in_days(n):
    return timezone.localdate() + timedelta(days=n)


QUOTE = {
    "first_name": "Awa", "last_name": "Koné", "email": "awa@example.com",
    "phone": "+225 07 00 00 00 00", "destination_text": "Zanzibar", "consent": True,
    "services_requested": ["VOL", "ASSURANCE"], "country_code": "ci",
}


class QuoteRequestCreateTests(TestCase):
    def test_valid_request_is_ready_for_the_service(self):
        serializer = QuoteRequestCreateSerializer(data=QUOTE)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        data = serializer.validated_data
        self.assertEqual(data["country_code"], "CI")
        self.assertNotIn("website", data)
        self.assertTrue(data["consent"])

    def test_errors(self):
        cases = {
            "consent": {**QUOTE, "consent": False},
            "website": {**QUOTE, "website": "http://spam.example"},
            "date_departure": {**QUOTE, "date_departure": in_days(-1)},
            "date_return": {**QUOTE, "date_departure": in_days(10), "date_return": in_days(5)},
            "destination_text": {**QUOTE, "destination_text": ""},
            "phone": {**QUOTE, "phone": "appelez-moi"},
            "services_requested": {**QUOTE, "services_requested": ["TELEPORTATION"]},
        }
        for field, payload in cases.items():
            with self.subTest(field=field):
                serializer = QuoteRequestCreateSerializer(data=payload)
                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)

    def test_destination_must_be_published(self):
        hidden = make_destination(is_published=False)
        serializer = QuoteRequestCreateSerializer(
            data={**QUOTE, "destination_text": "", "destination": hidden.slug}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("destination", serializer.errors)


class BookingRequestTests(TestCase):
    CONTACT = {"contact_name": "Awa", "contact_email": "awa@example.com",
               "contact_phone": "+2250700000000"}

    def test_items_become_item_requests_and_prices_are_ignored(self):
        serializer = BookingRequestSerializer(data={**self.CONTACT, "items": [
            {"kind": "vehicle", "object_id": 3, "start_date": in_days(2),
             "end_date": in_days(4), "unit_price": "1"},
            {"kind": "tour_departure", "object_id": 7, "quantity": 2},
        ]})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        items = serializer.validated_data["items"]
        self.assertEqual(items[1], ItemRequest("tour_departure", 7, quantity=2))
        self.assertFalse(hasattr(items[0], "unit_price"))

    def test_dates_are_required_by_kind(self):
        for item in (
            {"kind": "vehicle", "object_id": 1},
            {"kind": "room", "object_id": 1, "start_date": in_days(3), "end_date": in_days(3)},
            {"kind": "activity", "object_id": 1},
        ):
            with self.subTest(kind=item["kind"]):
                serializer = BookingRequestSerializer(data={**self.CONTACT, "items": [item]})
                self.assertFalse(serializer.is_valid())
                self.assertIn("items", serializer.errors)

    def test_at_least_one_item(self):
        serializer = BookingRequestSerializer(data={**self.CONTACT, "items": []})
        self.assertFalse(serializer.is_valid())


class ReviewCreateTests(TestCase):
    REVIEW = {"author_name": "Fatou", "author_email": "f@example.com", "rating": 5,
              "comment": "Un circuit inoubliable !"}

    def test_target_is_resolved_from_type_and_slug(self):
        tour = make_tour()
        serializer = ReviewCreateSerializer(
            data={**self.REVIEW, "target_type": "tour", "target_slug": tour.slug}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["tour"], tour)

    def test_unpublished_or_incomplete_target_is_refused(self):
        hidden = make_tour(is_published=False)
        for extra in ({"target_type": "tour", "target_slug": hidden.slug},
                      {"target_type": "tour"}):
            with self.subTest(extra=extra):
                self.assertFalse(ReviewCreateSerializer(data={**self.REVIEW, **extra}).is_valid())


class RegisterTests(TestCase):
    DATA = {"email": "Nouveau@Example.com", "password": "Voyage-Assinie-2027",
            "first_name": "Yao", "last_name": "Kouamé", "consent": True}

    def test_valid_registration(self):
        serializer = RegisterSerializer(data=self.DATA)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["email"], "nouveau@example.com")
        self.assertNotIn("consent", serializer.validated_data)

    def test_duplicate_email_weak_password_and_consent(self):
        make_user(email="nouveau@example.com")
        errors = RegisterSerializer(data={**self.DATA, "password": "123456",
                                          "consent": False})
        self.assertFalse(errors.is_valid())
        self.assertEqual(set(errors.errors), {"email", "consent"})
        weak = RegisterSerializer(data={**self.DATA, "email": "autre@example.com",
                                        "password": "123456"})
        self.assertFalse(weak.is_valid())
        self.assertIn("password", weak.errors)
