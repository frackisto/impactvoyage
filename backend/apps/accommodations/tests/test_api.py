from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.accommodations.models import Amenity
from apps.bookings.models import BookingItem
from apps.core.tests.factories import BookingFactory, ResidenceFactory, RoomFactory
from apps.core.tests.test_api import API, ApiTestCase


def in_days(n):
    return timezone.localdate() + timedelta(days=n)


def book(start, end, quantity=1, **target):
    return BookingItem.objects.create(
        booking=BookingFactory(), label="Test", unit_price=Decimal("1"), line_total=Decimal("1"),
        quantity=quantity, start_date=start, end_date=end, is_blocking=True, **target,
    )


class HotelSearchTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.double = RoomFactory(capacity=2, quantity=1, base_price=Decimal("45000"))
        self.hotel = self.double.hotel
        self.suite = RoomFactory(hotel=self.hotel, name="Suite", capacity=4, quantity=2,
                               base_price=Decimal("90000"))
        book(in_days(10), in_days(12), room=self.double)

    def price_from(self, **params):
        results = self.client.get(f"{API}/hotels/", params).data["results"]
        return results[0]["price_from"]["amount"] if results else None

    def test_price_from_matches_travelers_rooms_and_dates(self):
        self.assertEqual(self.price_from(), "45000.00")
        self.assertEqual(self.price_from(travelers=3), "90000.00")
        # Chambre double déjà réservée sur la période : seule la suite convient.
        period = {"available_from": in_days(11), "available_to": in_days(13)}
        self.assertEqual(self.price_from(**period), "90000.00")
        self.assertEqual(self.price_from(available_from=in_days(12), available_to=in_days(14)),
                         "45000.00")
        # 6 voyageurs dans 2 chambres : 3 par chambre, la suite (2 unités) convient.
        self.assertEqual(self.price_from(travelers=6, rooms=2), "90000.00")
        self.assertIsNone(self.price_from(rooms=3))

    def test_period_needs_both_dates(self):
        response = self.client.get(f"{API}/hotels/", {"available_from": in_days(3)})
        self.assertEqual(response.status_code, 400)

    def test_room_availability(self):
        url = f"{API}/hotels/{self.hotel.slug}/availability/"
        data = self.client.get(url, {"start": in_days(11), "end": in_days(13), "travelers": 3}).data
        by_room = {row["room"]: row for row in data}
        self.assertEqual(by_room[self.double.pk],
                         {"room": self.double.pk, "units_left": 0, "fits": False, "available": False})
        self.assertEqual(by_room[self.suite.pk],
                         {"room": self.suite.pk, "units_left": 2, "fits": True, "available": True})
        self.assertEqual(self.client.get(url, {"start": in_days(5)}).status_code, 400)


class ResidenceAvailabilityTests(ApiTestCase):
    def test_availability_and_booked_periods(self):
        residence = ResidenceFactory()
        book(in_days(10), in_days(14), residence=residence)
        url = f"{API}/residences/{residence.slug}/availability/"
        busy = self.client.get(url, {"start": in_days(12), "end": in_days(16)}).json()
        self.assertFalse(busy["available"])
        self.assertEqual(busy["booked_periods"], [[str(in_days(10)), str(in_days(14))]])
        free = self.client.get(url, {"start": in_days(14), "end": in_days(16)}).data
        self.assertTrue(free["available"])


class AmenityApiTests(ApiTestCase):
    def test_lists_only_amenities_in_use_and_filters_hotels(self):
        pool = Amenity.objects.create(name="Piscine")
        Amenity.objects.create(name="Sauna")  # utilisé par aucun hébergement
        hidden = Amenity.objects.create(name="Spa")
        for _ in range(2):
            RoomFactory().hotel.amenities.add(pool)
        RoomFactory()  # hôtel publié sans piscine
        unpublished = RoomFactory().hotel
        unpublished.is_published = False
        unpublished.save()
        unpublished.amenities.add(hidden)

        names = [a["name"] for a in self.client.get(f"{API}/amenities/").data]
        self.assertEqual(names, ["Piscine"])
        self.assertEqual(self.client.get(f"{API}/amenities/", {"kind": "residence"}).data, [])
        self.assertEqual(self.client.get(f"{API}/hotels/", {"amenities": pool.pk}).data["count"], 2)
        self.assertEqual(self.client.get(f"{API}/hotels/").data["count"], 3)
