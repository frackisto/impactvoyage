import re
from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.bookings.models import Booking, BookingItem
from apps.core.tests.helpers import (
    make_booking,
    make_departure,
    make_vehicle,
    make_vehicle_item,
)
from apps.inquiries.models import QuoteRequest


class ReferenceTests(TestCase):
    def test_booking_and_quote_get_readable_references(self):
        booking = make_booking()
        quote = QuoteRequest.objects.create(
            first_name="Awa", last_name="Koné", email="awa@example.com", phone="+225"
        )
        self.assertRegex(booking.reference, r"^IV-\d{4}-\d{6}$")
        self.assertRegex(quote.reference, r"^DV-\d{4}-\d{6}$")
        booking.refresh_from_db()
        self.assertTrue(re.match(r"^IV-", booking.reference))

    def test_soft_delete_hides_booking(self):
        booking = make_booking()
        booking.delete()
        self.assertFalse(Booking.objects.filter(pk=booking.pk).exists())
        self.assertTrue(Booking.all_objects.filter(pk=booking.pk).exists())


class BookingItemTargetTests(TestCase):
    def _item(self, **targets):
        return BookingItem.objects.create(
            booking=make_booking(), label="X", unit_price=Decimal("1"), line_total=Decimal("1"),
            start_date=date(2027, 1, 1), end_date=date(2027, 1, 2), **targets,
        )

    def test_item_needs_a_target(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._item()

    def test_item_cannot_have_two_targets(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._item(vehicle=make_vehicle(), tour_departure=make_departure())


class VehicleOverlapTests(TestCase):
    """Contrainte d'exclusion PostgreSQL bookingitem_vehicle_no_overlap."""

    def setUp(self):
        self.vehicle = make_vehicle()
        make_vehicle_item(make_booking(), self.vehicle, date(2027, 3, 1), date(2027, 3, 5))

    def test_overlapping_active_rentals_are_refused(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_vehicle_item(make_booking(), self.vehicle, date(2027, 3, 4), date(2027, 3, 8))

    def test_back_to_back_rentals_are_allowed(self):
        # end_date exclusive : restitution le 5, nouvelle location le 5.
        make_vehicle_item(make_booking(), self.vehicle, date(2027, 3, 5), date(2027, 3, 8))

    def test_non_blocking_requests_can_overlap(self):
        make_vehicle_item(
            make_booking(), self.vehicle, date(2027, 3, 2), date(2027, 3, 4), is_blocking=False
        )

    def test_confirming_an_overlapping_request_is_refused(self):
        request = make_vehicle_item(
            make_booking(), self.vehicle, date(2027, 3, 2), date(2027, 3, 4), is_blocking=False
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            BookingItem.objects.filter(pk=request.pk).update(is_blocking=True)

    def test_other_vehicle_is_free(self):
        make_vehicle_item(make_booking(), make_vehicle(), date(2027, 3, 1), date(2027, 3, 5))
