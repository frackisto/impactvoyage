"""
Fabriques de données de test (factory_boy, architecture § 14).

Chaque fabrique crée un objet valide avec des valeurs par défaut réalistes ;
un test ne précise que ce qui compte pour lui :

    tour = TourFactory(scope=Tour.Scope.INTERNATIONAL)
    departure = TourDepartureFactory(tour=tour, capacity=4)
    commercial = UserFactory(role="COMMERCIAL")

Les dates sont relatives à aujourd'hui : les tests ne vieillissent pas.
"""
from datetime import timedelta
from decimal import Decimal

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.accommodations.models import Hotel, Residence, Room
from apps.accounts.models import User
from apps.activities.models import Activity
from apps.blog.models import BlogPost
from apps.bookings.models import Booking, BookingItem
from apps.destinations.models import Destination
from apps.inquiries.models import ContactMessage, QuoteRequest
from apps.notifications.models import Notification
from apps.offers.models import Offer
from apps.reviews.models import Review
from apps.tours.models import Tour, TourDeparture
from apps.vehicles.models import Vehicle

PASSWORD = "mot-de-passe"


def in_days(days):
    return timezone.localdate() + timedelta(days=days)


class UserFactory(DjangoModelFactory):
    """Compte (client par défaut) ; mot de passe PASSWORD."""

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    role = User.Role.CLIENT

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", PASSWORD)
        return model_class.objects.create_user(password=password, **kwargs)


class DestinationFactory(DjangoModelFactory):
    class Meta:
        model = Destination

    name = factory.Sequence(lambda n: f"Destination {n}")
    slug = factory.Sequence(lambda n: f"destination-{n}")
    continent = Destination.Continent.AFRIQUE
    country_code = "CI"
    description = "Description"


class TourFactory(DjangoModelFactory):
    class Meta:
        model = Tour

    title = factory.Sequence(lambda n: f"Circuit {n}")
    slug = factory.Sequence(lambda n: f"circuit-{n}")
    description = "Description"
    destination = factory.SubFactory(DestinationFactory)
    scope = Tour.Scope.NATIONAL
    duration_days = 3
    base_price = Decimal("150000")


class TourDepartureFactory(DjangoModelFactory):
    class Meta:
        model = TourDeparture

    tour = factory.SubFactory(TourFactory)
    start_date = factory.LazyFunction(lambda: in_days(60))
    end_date = factory.LazyAttribute(lambda departure: departure.start_date + timedelta(days=3))
    capacity = 10


class HotelFactory(DjangoModelFactory):
    class Meta:
        model = Hotel

    name = factory.Sequence(lambda n: f"Hôtel {n}")
    slug = factory.Sequence(lambda n: f"hotel-{n}")
    description = "…"
    destination = factory.SubFactory(DestinationFactory)


class RoomFactory(DjangoModelFactory):
    class Meta:
        model = Room

    hotel = factory.SubFactory(HotelFactory)
    name = "Double"
    capacity = 2
    base_price = Decimal("45000")


class ResidenceFactory(DjangoModelFactory):
    class Meta:
        model = Residence

    name = factory.Sequence(lambda n: f"Résidence {n}")
    slug = factory.Sequence(lambda n: f"residence-{n}")
    description = "…"
    destination = factory.SubFactory(DestinationFactory)
    rooms_count = 2
    capacity = 4
    base_price = Decimal("70000")


class VehicleFactory(DjangoModelFactory):
    class Meta:
        model = Vehicle

    brand = "Toyota"
    model = "Prado"
    slug = factory.Sequence(lambda n: f"toyota-prado-{n}")
    category = Vehicle.Category.QUATRE_QUATRE
    year = 2023
    plate_number = factory.Sequence(lambda n: f"AB-{n:04d}-CI")
    seats = 7
    transmission = Vehicle.Transmission.AUTOMATIQUE
    fuel = Vehicle.Fuel.DIESEL
    base_price = Decimal("60000")


class ActivityFactory(DjangoModelFactory):
    class Meta:
        model = Activity

    title = factory.Sequence(lambda n: f"Activité {n}")
    slug = factory.Sequence(lambda n: f"activite-{n}")
    description = "…"
    destination = factory.SubFactory(DestinationFactory)
    duration_hours = Decimal("3")
    base_price = Decimal("20000")


class BookingFactory(DjangoModelFactory):
    """Réservation sans ligne (statut « Demande reçue ») ; voir BookingItemFactory."""

    class Meta:
        model = Booking

    contact_name = "Awa Koné"
    contact_email = "awa@example.com"
    contact_phone = "+2250700000000"


class BookingItemFactory(DjangoModelFactory):
    """Location de véhicule de 3 jours dans 10 jours, qui bloque le véhicule."""

    class Meta:
        model = BookingItem

    booking = factory.SubFactory(BookingFactory)
    vehicle = factory.SubFactory(VehicleFactory)
    label = factory.LazyAttribute(lambda item: str(item.vehicle))
    start_date = factory.LazyFunction(lambda: in_days(10))
    end_date = factory.LazyAttribute(lambda item: item.start_date + timedelta(days=3))
    unit_price = factory.LazyAttribute(lambda item: item.vehicle.base_price)
    line_total = factory.LazyAttribute(
        lambda item: item.unit_price * (item.end_date - item.start_date).days
    )
    is_blocking = True


class QuoteRequestFactory(DjangoModelFactory):
    class Meta:
        model = QuoteRequest

    first_name = "Awa"
    last_name = "Koné"
    email = "awa@example.com"
    phone = "+2250700000000"
    destination_text = "Dubaï"
    consent_at = factory.LazyFunction(timezone.now)


class ContactMessageFactory(DjangoModelFactory):
    class Meta:
        model = ContactMessage

    name = "Koffi"
    email = "koffi@example.com"
    subject = "Visa Canada"
    message = "Bonjour…"


class ReviewFactory(DjangoModelFactory):
    class Meta:
        model = Review

    author_name = "Mariam"
    author_email = "mariam@example.com"
    rating = 5
    comment = "Parfait"


class OfferFactory(DjangoModelFactory):
    """Offre de circuit en cours (depuis hier, pour 10 jours), 25 % de réduction."""

    class Meta:
        model = Offer

    title = "Offre"
    slug = factory.Sequence(lambda n: f"offre-{n}")
    offer_type = Offer.OfferType.CIRCUIT
    initial_price = Decimal("200000")
    promo_price = Decimal("150000")
    start_date = factory.LazyFunction(lambda: in_days(-1))
    end_date = factory.LazyFunction(lambda: in_days(10))


class BlogPostFactory(DjangoModelFactory):
    """Article en brouillon."""

    class Meta:
        model = BlogPost

    title = factory.Sequence(lambda n: f"Article {n}")
    slug = factory.Sequence(lambda n: f"article-{n}")
    excerpt = "Résumé de l'article."
    content = "Contenu de l'article."


class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification

    recipient = factory.SubFactory(UserFactory, role=User.Role.ADMIN)
    event = Notification.Event.CONTACT_RECEIVED
    title = "Message de Koffi"
    link = "/admin/inquiries/contactmessage/"
