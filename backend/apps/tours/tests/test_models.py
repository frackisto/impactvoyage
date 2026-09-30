from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import F, ProtectedError
from django.test import TestCase

from apps.bookings.models import BookingItem
from apps.core.tests.factories import BookingFactory, TourDepartureFactory, TourFactory
from apps.tours.models import TourDeparture


class TourDepartureTests(TestCase):
    def test_cannot_reserve_more_seats_than_capacity(self):
        departure = TourDepartureFactory(capacity=2)
        TourDeparture.objects.filter(pk=departure.pk).update(seats_reserved=F("seats_reserved") + 2)
        with self.assertRaises(IntegrityError), transaction.atomic():
            TourDeparture.objects.filter(pk=departure.pk).update(
                seats_reserved=F("seats_reserved") + 1
            )

    def test_end_date_cannot_precede_start_date(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            TourDepartureFactory(start_date=date(2027, 1, 10), end_date=date(2027, 1, 9))

    def test_one_departure_per_day_and_tour(self):
        tour = TourFactory()
        TourDepartureFactory(tour=tour)
        with self.assertRaises(IntegrityError), transaction.atomic():
            TourDepartureFactory(tour=tour)

    def test_price_and_seats_left(self):
        departure = TourDepartureFactory(capacity=10, seats_reserved=4)
        self.assertEqual(departure.seats_left, 6)
        self.assertEqual(departure.price, Decimal("150000"))
        departure.price_override = Decimal("120000")
        self.assertEqual(departure.price, Decimal("120000"))

    def test_tour_max_travelers_not_below_min(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            TourFactory(min_travelers=4, max_travelers=2)

    def test_booked_departure_protects_tour_from_deletion(self):
        departure = TourDepartureFactory()
        BookingItem.objects.create(
            booking=BookingFactory(), tour_departure=departure, label="Circuit",
            unit_price=Decimal("150000"), line_total=Decimal("150000"),
            start_date=departure.start_date, end_date=departure.end_date,
        )
        with self.assertRaises(ProtectedError):
            departure.tour.delete()

    def test_unbooked_departures_are_deleted_with_tour(self):
        departure = TourDepartureFactory()
        departure.tour.delete()
        self.assertFalse(TourDeparture.objects.exists())
