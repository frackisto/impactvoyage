"""
Règles de tarification et de validation des demandes (bookings.services.price_item) :
chaque demande impossible est refusée avec un code stable, exploité par le frontend.
"""
from decimal import Decimal

from django.test import TestCase

from apps.bookings import services
from apps.bookings.services import ItemRequest
from apps.core.choices import Currency
from apps.core.exceptions import BusinessError, NotAvailable
from apps.core.tests.factories import (
    ActivityFactory,
    ResidenceFactory,
    RoomFactory,
    TourDepartureFactory,
    VehicleFactory,
    in_days,
)
from apps.tours.models import TourDeparture


class PricingRulesTests(TestCase):
    def setUp(self):
        self.departure = TourDepartureFactory(start_date=in_days(20), end_date=in_days(23))
        self.room = RoomFactory(quantity=2)
        self.residence = ResidenceFactory()
        self.vehicle = VehicleFactory()
        self.activity = ActivityFactory(max_participants=8)

    def assert_refused(self, request, code, error=BusinessError):
        with self.assertRaises(error) as raised:
            services.price_item(request)
        self.assertEqual(raised.exception.code, code)

    def test_invalid_requests_are_refused_with_a_stable_code(self):
        cases = [
            ("type inconnu", ItemRequest("cruise", 1), "unknown_kind"),
            ("quantité nulle", ItemRequest("room", self.room.pk, in_days(5), in_days(7), quantity=0),
             "invalid_quantity"),
            ("offre introuvable", ItemRequest("tour_departure", 999999), "offer_not_found"),
            ("chambre introuvable", ItemRequest("room", 999999, in_days(5), in_days(7)), "offer_not_found"),
            ("résidence introuvable", ItemRequest("residence", 999999, in_days(5), in_days(7)),
             "offer_not_found"),
            ("activité introuvable", ItemRequest("activity", 999999, in_days(5)), "offer_not_found"),
            ("dates absentes", ItemRequest("vehicle", self.vehicle.pk), "dates_required"),
            ("date passée", ItemRequest("residence", self.residence.pk, in_days(-1), in_days(2)),
             "date_in_past"),
            ("période vide", ItemRequest("vehicle", self.vehicle.pk, in_days(5), in_days(5)),
             "invalid_period"),
            ("activité passée", ItemRequest("activity", self.activity.pk, in_days(-2)), "date_in_past"),
        ]
        for label, request, code in cases:
            with self.subTest(label):
                self.assert_refused(request, code)

    def test_unavailable_offers(self):
        cases = [
            ("trop de chambres", ItemRequest("room", self.room.pk, in_days(5), in_days(7), quantity=3)),
            ("trop de participants", ItemRequest("activity", self.activity.pk, in_days(5), quantity=9)),
            ("trop de voyageurs", ItemRequest("tour_departure", self.departure.pk, quantity=11)),
        ]
        for label, request in cases:
            with self.subTest(label):
                self.assert_refused(request, "not_available", NotAvailable)

        TourDeparture.objects.filter(pk=self.departure.pk).update(status=TourDeparture.Status.CANCELLED)
        self.assert_refused(ItemRequest("tour_departure", self.departure.pk), "not_available", NotAvailable)

    def test_prices_are_computed_server_side(self):
        room = services.price_item(ItemRequest("room", self.room.pk, in_days(5), in_days(8), quantity=2))
        self.assertEqual(room.item.line_total, Decimal("45000") * 3 * 2)  # 3 nuits, 2 chambres
        car = services.price_item(ItemRequest("vehicle", self.vehicle.pk, in_days(5), in_days(9),
                                              pickup_location="Aéroport"))
        self.assertEqual(car.item.line_total, Decimal("60000") * 4)
        self.assertEqual(car.item.pickup_location, "Aéroport")
        visit = services.price_item(ItemRequest("activity", self.activity.pk, in_days(5), quantity=3))
        self.assertEqual(visit.item.end_date, in_days(6))
        self.assertEqual(visit.item.line_total, Decimal("20000") * 3)

    def test_one_currency_per_booking(self):
        euro_car = VehicleFactory(currency=Currency.EUR)
        with self.assertRaises(BusinessError) as raised:
            services.request_booking(
                contact_name="Awa", contact_email="awa@example.com", contact_phone="0102030405",
                items=[ItemRequest("vehicle", self.vehicle.pk, in_days(5), in_days(6)),
                       ItemRequest("vehicle", euro_car.pk, in_days(5), in_days(6))],
            )
        self.assertEqual(raised.exception.code, "mixed_currencies")
