"""
Données de démonstration (architecture § 14) : circuits nationaux et
internationaux (programme, départs), hôtels (chambres, équipements), résidence,
véhicules, activités, événements et avis, avec des réservations confirmées pour
illustrer les disponibilités. Fictives mais cohérentes.

    python manage.py seed_demo          # charge le contenu de l'agence puis la démo
    python manage.py seed_demo --reset  # supprime les données de démonstration

Idempotent. Refusé si DEMO_DATA_ALLOWED est faux (production).
Les phases suivantes ajouteront offres et comptes.
"""
from datetime import date, timedelta
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accommodations.models import Amenity, Hotel, HotelImage, Residence, Room
from apps.activities.models import Activity, ActivityImage
from apps.bookings.models import Booking, BookingItem
from apps.core import demo_content as demo
from apps.core.models import Category
from apps.destinations.models import Destination
from apps.events.models import Event, EventImage
from apps.reviews.models import Review
from apps.tours.models import Tour, TourDay, TourDeparture, TourImage
from apps.vehicles.models import Vehicle, VehicleImage

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "agency"


def translated(field, values):
    """("titre FR", "titre EN") → {"field": FR, "field_fr": FR, "field_en": EN}."""
    fr, en = values
    return {field: fr, f"{field}_fr": fr, f"{field}_en": en}


class Command(BaseCommand):
    help = "Charge (ou supprime avec --reset) les données de démonstration. Interdit en production."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Supprime les données de démonstration.")

    def handle(self, *args, reset=False, **options):
        if not getattr(settings, "DEMO_DATA_ALLOWED", False):
            raise CommandError("Données de démonstration interdites ici (DEMO_DATA_ALLOWED = False).")
        if reset:
            counts = self.reset()
            self.stdout.write(self.style.SUCCESS(
                "Démonstration supprimée : " + ", ".join(f"{n} {label}" for label, n in counts.items()) + "."
            ))
            return
        # Destinations, thèmes et photos viennent du contenu réel de l'agence.
        call_command("load_agency_content", verbosity=0)
        with transaction.atomic():
            counts = {"circuits": self.tours()}
            amenities = self.amenities()
            counts["hôtels"] = self.hotels(amenities)
            counts["résidences"] = self.residences(amenities)
            counts["véhicules"] = self.vehicles()
            counts["activités"] = self.activities()
            counts["événements"] = self.events()
            self.bookings()
            counts["avis"] = self.reviews()
        self.stdout.write(self.style.SUCCESS(
            "Démonstration chargée : " + ", ".join(f"{n} {label}" for label, n in counts.items()) + "."
        ))

    @transaction.atomic
    def reset(self):
        """Supprime les contenus de démonstration (avis, départs, chambres : en cascade)."""
        # Réservations fictives d'abord : leurs lignes protègent les offres (PROTECT).
        Booking.objects.filter(contact_email=demo.DEMO_EMAIL).delete()
        counts = {}
        for label, model, items in [
            ("circuits", Tour, demo.TOURS), ("hôtels", Hotel, demo.HOTELS),
            ("résidences", Residence, demo.RESIDENCES), ("véhicules", Vehicle, demo.VEHICLES),
            ("activités", Activity, demo.ACTIVITIES), ("événements", Event, demo.EVENTS),
        ]:
            deleted = model.objects.filter(slug__in=[item["slug"] for item in items])
            counts[label] = deleted.count()
            deleted.delete()
        Category.objects.filter(
            kind=Category.Kind.ACTIVITY, slug__in=[slug for slug, _, _ in demo.ACTIVITY_CATEGORIES],
            activities__isnull=True,
        ).delete()
        return counts

    def activities(self):
        categories = {}
        for order, (slug, fr, en) in enumerate(demo.ACTIVITY_CATEGORIES):
            categories[slug], _ = Category.objects.update_or_create(
                kind=Category.Kind.ACTIVITY, slug=slug, defaults={"name_fr": fr, "name_en": en, "order": order},
            )
        for item in demo.ACTIVITIES:
            activity, _ = Activity.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    **translated("title", item["title"]),
                    **translated("short_description", item["short"]),
                    **translated("description", item["description"]),
                    **translated("cover_alt", item["title"]),
                    "destination": Destination.objects.get(slug=item["destination"]),
                    "category": categories[item["category"]],
                    "duration_hours": demo.price(item["hours"]),
                    "max_participants": item["max"],
                    "base_price": demo.price(item["price"]),
                    "is_published": True,
                },
            )
            self.photos(activity, item["cover"], [], ActivityImage, "activity", item["title"])
        for tour_slug, activity_slugs in demo.TOUR_ACTIVITIES:
            Tour.objects.get(slug=tour_slug).activities.set(Activity.objects.filter(slug__in=activity_slugs))
        return len(demo.ACTIVITIES)

    def events(self):
        for item in demo.EVENTS:
            event, _ = Event.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    **translated("title", item["title"]),
                    **translated("short_description", item["short"]),
                    **translated("description", item["description"]),
                    **translated("location", (item["location"], item["location"])),
                    **translated("cover_alt", item["title"]),
                    "category": item["category"],
                    "date": date(*item["date"]),
                    "end_date": date(*item["end"]) if item["end"] else None,
                    "destination": Destination.objects.get(slug=item["destination"]),
                    "participants_count": item["participants"],
                    "is_published": True,
                },
            )
            if item["cover"] and not event.cover_image:
                with open(FIXTURES / item["cover"], "rb") as handle:
                    event.cover_image.save(item["cover"], File(handle), save=True)
            if not event.media.exists():
                for order, filename in enumerate(item["gallery"]):
                    photo = EventImage(event=event, type=EventImage.Type.PHOTO, order=order,
                                       **translated("alt_text", item["title"]))
                    with open(FIXTURES / filename, "rb") as handle:
                        photo.image.save(filename, File(handle), save=False)
                    photo.save()
        return len(demo.EVENTS)

    def vehicles(self):
        for number, item in enumerate(demo.VEHICLES, start=1):
            vehicle, _ = Vehicle.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "brand": item["brand"], "model": item["model"], "category": item["category"],
                    "year": item["year"], "seats": item["seats"], "transmission": item["transmission"],
                    "fuel": item["fuel"], "features": item["features"],
                    "plate_number": f"DEMO-{number:03d}",
                    **translated("description", item["description"]),
                    **translated("cover_alt", (f"{item['brand']} {item['model']}",) * 2),
                    "base_price": demo.price(item["price"]),
                    "is_featured": item["featured"], "is_published": True,
                },
            )
            alt = (f"{item['brand']} {item['model']}",) * 2
            self.photos(vehicle, item["cover"], item["gallery"], VehicleImage, "vehicle", alt)
        return len(demo.VEHICLES)

    def bookings(self):
        """Réservations confirmées fictives, recréées à chaque chargement (dates relatives)."""
        Booking.objects.filter(contact_email=demo.DEMO_EMAIL).delete()
        today = timezone.localdate()
        for slug, in_days, days in demo.VEHICLE_BOOKINGS:
            vehicle = Vehicle.objects.get(slug=slug)
            total = vehicle.base_price * days
            booking = Booking.objects.create(
                contact_name="Client de démonstration", contact_email=demo.DEMO_EMAIL,
                contact_phone="+2250700000000", status=Booking.Status.CONFIRMED, total_amount=total,
            )
            start = today + timedelta(days=in_days)
            BookingItem.objects.create(
                booking=booking, vehicle=vehicle, label=str(vehicle), unit_price=vehicle.base_price,
                line_total=total, start_date=start, end_date=start + timedelta(days=days),
                is_blocking=True,
            )
        for slug, in_days, participants in demo.ACTIVITY_BOOKINGS:
            activity = Activity.objects.get(slug=slug)
            total = activity.base_price * participants
            booking = Booking.objects.create(
                contact_name="Groupe de démonstration", contact_email=demo.DEMO_EMAIL,
                contact_phone="+2250700000000", status=Booking.Status.CONFIRMED, total_amount=total,
            )
            day = today + timedelta(days=in_days)
            BookingItem.objects.create(
                booking=booking, activity=activity, label=str(activity), unit_price=activity.base_price,
                quantity=participants, line_total=total, start_date=day, end_date=day + timedelta(days=1),
                is_blocking=True,
            )

    def tours(self):
        today = timezone.localdate()
        themes = {c.slug: c for c in Category.objects.filter(kind=Category.Kind.TOUR_THEME)}
        for item in demo.TOURS:
            tour, _ = Tour.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    **translated("title", item["title"]),
                    **translated("short_description", item["short"]),
                    **translated("description", item["description"]),
                    **translated("departure_points", item["departure_points"]),
                    **translated("transport_info", item["transport"]),
                    **translated("accommodation_info", item["accommodation"]),
                    **translated("inclusions", item["inclusions"]),
                    **translated("exclusions", item["exclusions"]),
                    **translated("conditions", item["conditions"]),
                    **translated("cover_alt", item["title"]),
                    "destination": Destination.objects.get(slug=item["destination"]),
                    "scope": item["scope"],
                    "theme": themes.get(item["theme"]),
                    "is_custom": item.get("is_custom", False),
                    "duration_days": item["duration"],
                    "min_travelers": item["min"],
                    "max_travelers": item["max"],
                    "base_price": demo.price(item["price"]),
                    "is_featured": item["featured"],
                    "is_published": True,
                },
            )
            tour.days.all().delete()
            TourDay.objects.bulk_create([
                TourDay(
                    tour=tour, day_number=number,
                    **translated("title", (title_fr, title_en)),
                    **translated("description", (desc_fr, desc_en)),
                )
                for number, (title_fr, title_en, desc_fr, desc_en) in enumerate(item["days"], start=1)
            ])
            for weeks, capacity, reserved, override in item["departures"]:
                start = today + timedelta(weeks=weeks)
                TourDeparture.objects.update_or_create(
                    tour=tour, start_date=start,
                    defaults={
                        "end_date": start + timedelta(days=item["duration"] - 1),
                        "capacity": capacity, "seats_reserved": reserved,
                        "price_override": demo.price(override),
                    },
                )
            self.photos(tour, item["cover"], item["gallery"], TourImage, "tour", item["title"])
        return len(demo.TOURS)

    def amenities(self):
        result = {}
        for name_fr, name_en, icon in demo.AMENITIES:
            amenity, _ = Amenity.objects.update_or_create(
                name_fr=name_fr,
                defaults={"name": name_fr, "name_en": name_en, "icon": icon, "scope": Amenity.Scope.BOTH},
            )
            result[name_fr] = amenity
        return result

    def hotels(self, amenities):
        for item in demo.HOTELS:
            hotel, _ = Hotel.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    **translated("short_description", item["short"]),
                    **translated("description", item["description"]),
                    **translated("cover_alt", (item["name"], item["name"])),
                    "destination": Destination.objects.get(slug=item["destination"]),
                    "address": item["address"],
                    "accommodation_type": item["type"],
                    "stars": item["stars"],
                    "is_featured": item["featured"],
                    "is_published": True,
                },
            )
            hotel.amenities.set([amenities[name] for name in item["amenities"]])
            for name_fr, name_en, desc_fr, desc_en, capacity, quantity, price in item["rooms"]:
                Room.objects.update_or_create(
                    hotel=hotel, name_fr=name_fr,
                    defaults={
                        **translated("name", (name_fr, name_en)),
                        **translated("description", (desc_fr, desc_en)),
                        "capacity": capacity, "quantity": quantity,
                        "base_price": demo.price(price), "is_active": True,
                    },
                )
            alt = (item["name"], item["name"])
            self.photos(hotel, item["cover"], item["gallery"], HotelImage, "hotel", alt)
        return len(demo.HOTELS)

    def residences(self, amenities):
        for item in demo.RESIDENCES:
            residence, _ = Residence.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    **translated("short_description", item["short"]),
                    **translated("description", item["description"]),
                    **translated("services", item["services"]),
                    **translated("conditions", item["conditions"]),
                    **translated("cover_alt", (item["name"], item["name"])),
                    "destination": Destination.objects.get(slug=item["destination"]),
                    "address": item["address"],
                    "rooms_count": item["rooms"], "capacity": item["capacity"],
                    "base_price": demo.price(item["price"]),
                    "is_published": True,
                },
            )
            residence.amenities.set([amenities[name] for name in item["amenities"]])
        return len(demo.RESIDENCES)

    def photos(self, obj, cover, gallery, image_model, owner_field, alt):
        """Photo principale et galerie depuis les fixtures, seulement si absentes."""
        if cover and not obj.cover_image:
            with open(FIXTURES / cover, "rb") as handle:
                obj.cover_image.save(cover, File(handle), save=True)
        if obj.images.exists():
            return
        for order, filename in enumerate(gallery):
            image = image_model(**{owner_field: obj}, order=order, **translated("alt_text", alt))
            with open(FIXTURES / filename, "rb") as handle:
                image.image.save(filename, File(handle), save=False)
            image.save()

    def reviews(self):
        targets = [("tour", Tour, row) for row in demo.TOUR_REVIEWS]
        targets += [("hotel", Hotel, row) for row in demo.HOTEL_REVIEWS]
        for field, model, (slug, author, rating, comment) in targets:
            Review.objects.update_or_create(
                **{field: model.objects.get(slug=slug)}, author_name=author,
                defaults={
                    "author_email": demo.DEMO_EMAIL, "rating": rating, "comment": comment,
                    "status": Review.Status.APPROUVE,
                },
            )
        return len(targets)
