from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from apps.accommodations.selectors import hotel_list
from apps.bookings import services as booking_services
from apps.bookings.services import ItemRequest
from apps.core.exceptions import BusinessError
from apps.core.formatting import format_amount
from apps.core.models import ExchangeRate
from apps.core.services import convert_from_xof, get_rates, update_exchange_rates
from apps.core.tests.factories import (
    RoomFactory,
    TourDepartureFactory,
    TourFactory,
    VehicleFactory,
)
from apps.tours.selectors import tour_list
from apps.vehicles.selectors import vehicle_list


def fake_fetch(symbols):
    return {"USD": Decimal("1.10"), "GBP": Decimal("0.85")}


class CurrencyTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_update_rates_uses_the_fixed_euro_peg(self):
        with self.captureOnCommitCallbacks(execute=True):
            update_exchange_rates(fetch=fake_fetch)
        self.assertEqual(ExchangeRate.objects.count(), 3)
        self.assertEqual(convert_from_xof(655957, "EUR"), Decimal("1000.00"))
        self.assertEqual(convert_from_xof(655957, "USD"), Decimal("1100.00"))
        self.assertEqual(convert_from_xof(Decimal("125000.4"), "XOF"), Decimal("125000"))

    def test_unknown_currency(self):
        get_rates()
        with self.assertRaises(BusinessError):
            convert_from_xof(1000, "JPY")

    def test_format_amount(self):
        self.assertEqual(format_amount(Decimal("1250000"), "XOF"), "1 250 000 FCFA")
        self.assertEqual(format_amount(Decimal("12.5"), "EUR"), "12,50 EUR")


def in_days(n):
    return timezone.localdate() + timedelta(days=n)


class CatalogSelectorTests(TestCase):
    def test_tour_search_by_travelers_and_dates(self):
        small = TourDepartureFactory(start_date=in_days(20), end_date=in_days(22), capacity=2)
        big = TourDepartureFactory(start_date=in_days(40), end_date=in_days(42), capacity=20)
        TourFactory()  # sans départ : exclu dès qu'on filtre sur les départs

        self.assertEqual(set(tour_list(travelers=5)), {big.tour})
        self.assertEqual(set(tour_list(departure_to=in_days(30))), {small.tour})
        self.assertEqual(tour_list().get(pk=small.tour.pk).next_departure, small.start_date)

    def test_vehicle_search_excludes_booked_vehicles(self):
        booked, free = VehicleFactory(), VehicleFactory()
        booking_services.confirm_booking(booking_services.request_booking(
            contact_name="A", contact_email="a@example.com", contact_phone="1",
            items=[ItemRequest("vehicle", booked.pk, in_days(10), in_days(15))],
        ))
        self.assertEqual(
            set(vehicle_list(available_from=in_days(12), available_to=in_days(13))), {free}
        )
        self.assertEqual(
            set(vehicle_list(available_from=in_days(15), available_to=in_days(18))),
            {booked, free},
        )

    def test_hotel_price_from_is_the_cheapest_active_room(self):
        room = RoomFactory(base_price=Decimal("60000"))
        RoomFactory(hotel=room.hotel, base_price=Decimal("40000"), capacity=1)
        RoomFactory(hotel=room.hotel, base_price=Decimal("10000"), is_active=False)
        self.assertEqual(hotel_list().get().price_from, Decimal("40000"))
        self.assertEqual(hotel_list(travelers=2).get().price_from, Decimal("60000"))
