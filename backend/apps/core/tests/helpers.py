"""Constructeurs minimaux pour les tests (remplacés par factory_boy en Phase 22)."""
from datetime import date
from decimal import Decimal
from itertools import count

from django.contrib.auth import get_user_model

from apps.accommodations.models import Hotel, Residence, Room
from apps.activities.models import Activity
from apps.bookings.models import Booking, BookingItem
from apps.destinations.models import Destination
from apps.tours.models import Tour, TourDeparture
from apps.vehicles.models import Vehicle

_seq = count(1)


def make_destination(**kwargs):
    n = next(_seq)
    defaults = {
        "name": f"Destination {n}",
        "slug": f"destination-{n}",
        "continent": Destination.Continent.AFRIQUE,
        "country_code": "CI",
        "description": "Description",
    }
    return Destination.objects.create(**{**defaults, **kwargs})


def make_tour(**kwargs):
    n = next(_seq)
    defaults = {
        "title": f"Circuit {n}",
        "slug": f"circuit-{n}",
        "description": "Description",
        "destination": kwargs.pop("destination", None) or make_destination(),
        "scope": Tour.Scope.NATIONAL,
        "duration_days": 3,
        "base_price": Decimal("150000"),
    }
    return Tour.objects.create(**{**defaults, **kwargs})


def make_departure(**kwargs):
    defaults = {
        "tour": kwargs.pop("tour", None) or make_tour(),
        "start_date": date(2027, 1, 10),
        "end_date": date(2027, 1, 13),
        "capacity": 10,
    }
    return TourDeparture.objects.create(**{**defaults, **kwargs})


def make_vehicle(**kwargs):
    n = next(_seq)
    defaults = {
        "brand": "Toyota",
        "model": "Prado",
        "slug": f"toyota-prado-{n}",
        "category": Vehicle.Category.QUATRE_QUATRE,
        "year": 2023,
        "plate_number": f"AB-{n:04d}-CI",
        "seats": 7,
        "transmission": Vehicle.Transmission.AUTOMATIQUE,
        "fuel": Vehicle.Fuel.DIESEL,
        "base_price": Decimal("60000"),
    }
    return Vehicle.objects.create(**{**defaults, **kwargs})


def make_booking(**kwargs):
    defaults = {
        "contact_name": "Awa Koné",
        "contact_email": "awa@example.com",
        "contact_phone": "+2250700000000",
    }
    return Booking.objects.create(**{**defaults, **kwargs})


def make_vehicle_item(booking, vehicle, start, end, is_blocking=True):
    return BookingItem.objects.create(
        booking=booking,
        vehicle=vehicle,
        label=str(vehicle),
        unit_price=vehicle.base_price,
        line_total=vehicle.base_price * (end - start).days,
        start_date=start,
        end_date=end,
        is_blocking=is_blocking,
    )


def make_user(role="CLIENT", **kwargs):
    n = next(_seq)
    return get_user_model().objects.create_user(
        kwargs.pop("email", f"user{n}@example.com"), "mot-de-passe", role=role, **kwargs
    )


def make_room(**kwargs):
    n = next(_seq)
    hotel = kwargs.pop("hotel", None) or Hotel.objects.create(
        name=f"Hôtel {n}", slug=f"hotel-{n}", description="…", destination=make_destination()
    )
    defaults = {"hotel": hotel, "name": "Double", "capacity": 2, "base_price": Decimal("45000")}
    return Room.objects.create(**{**defaults, **kwargs})


def make_residence(**kwargs):
    n = next(_seq)
    defaults = {
        "name": f"Résidence {n}", "slug": f"residence-{n}", "description": "…",
        "destination": make_destination(), "rooms_count": 2, "capacity": 4,
        "base_price": Decimal("70000"),
    }
    return Residence.objects.create(**{**defaults, **kwargs})


def make_activity(**kwargs):
    n = next(_seq)
    defaults = {
        "title": f"Activité {n}", "slug": f"activite-{n}", "description": "…",
        "destination": make_destination(), "duration_hours": Decimal("3"),
        "base_price": Decimal("20000"),
    }
    return Activity.objects.create(**{**defaults, **kwargs})
