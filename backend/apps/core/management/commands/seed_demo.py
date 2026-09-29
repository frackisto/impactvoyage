"""
Données de démonstration (architecture § 14) : circuits nationaux et
internationaux (programme, départs), hôtels (chambres, équipements), résidence,
véhicules, activités, événements, devis, offres, transports, albums de la
médiathèque, articles de blog et avis, avec des réservations confirmées pour
illustrer les disponibilités. Fictives mais cohérentes.

    python manage.py seed_demo          # charge le contenu de l'agence puis la démo
    python manage.py seed_demo --reset  # supprime les données de démonstration

Idempotent. Refusé si DEMO_DATA_ALLOWED est faux (production).
Comptes de l'équipe : un par rôle pour essayer le backoffice (voir le README).
"""
import uuid
from datetime import date, timedelta
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accommodations.models import Amenity, Hotel, HotelImage, Residence, Room
from apps.accounts.models import User
from apps.activities.models import Activity, ActivityImage
from apps.blog.models import BlogPost
from apps.bookings.models import Booking, BookingItem
from apps.core import demo_content as demo
from apps.core.models import Category, Tag
from apps.destinations.models import Destination
from apps.events.models import Event, EventImage
from apps.inquiries.models import QuoteRequest
from apps.media.models import MediaAlbum, MediaItem
from apps.offers.models import Offer
from apps.reviews.models import Review
from apps.tours.models import Tour, TourDay, TourDeparture, TourImage
from apps.transport.models import TransportService
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
            counts["devis"] = self.quotes()
            counts["offres"] = self.offers()
            counts["transports"] = self.transports()
            counts["albums"] = self.albums()
            counts["articles"] = self.posts()
            counts["avis"] = self.reviews()
            counts["comptes de l'équipe"] = self.staff_accounts()
        self.stdout.write(self.style.SUCCESS(
            "Démonstration chargée : " + ", ".join(f"{n} {label}" for label, n in counts.items()) + "."
        ))

    @transaction.atomic
    def reset(self):
        """Supprime les contenus de démonstration (avis, départs, chambres : en cascade)."""
        # Réservations fictives d'abord : leurs lignes protègent les offres (PROTECT).
        # QuerySet.delete() supprime réellement, y compris les objets à suppression logique.
        Booking.all_objects.filter(contact_email=demo.DEMO_EMAIL).delete()
        counts = {"devis": QuoteRequest.all_objects.filter(email=demo.DEMO_EMAIL).delete()[0]}
        staff = User.objects.filter(email__in=[email for email, _, _ in demo.STAFF_ACCOUNTS])
        counts["comptes de l'équipe"] = staff.count()
        staff.delete()
        # Offres en premier : celles qui ciblent une fiche disparaîtraient avec elle (CASCADE).
        for label, model, items in [
            ("offres", Offer, demo.OFFERS), ("transports", TransportService, demo.TRANSPORTS),
            ("albums", MediaAlbum, demo.ALBUMS), ("articles", BlogPost, demo.BLOG_POSTS),
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
        Category.objects.filter(
            kind=Category.Kind.MEDIA, slug__in=[slug for slug, _, _ in demo.MEDIA_CATEGORIES],
            media_albums__isnull=True,
        ).delete()
        Category.objects.filter(
            kind=Category.Kind.BLOG, slug__in=[slug for slug, _, _ in demo.BLOG_CATEGORIES],
            blog_posts__isnull=True,
        ).delete()
        Tag.objects.filter(
            slug__in=[slug for post in demo.BLOG_POSTS for slug, _, _ in post["tags"]],
            blog_posts__isnull=True,
        ).delete()
        return counts

    def staff_accounts(self):
        """Un compte par rôle de l'équipe, mot de passe de démonstration rétabli à chaque chargement."""
        for email, role, first_name in demo.STAFF_ACCOUNTS:
            user, _ = User.objects.update_or_create(
                email=email,
                defaults={"role": role, "first_name": first_name, "last_name": "Démo",
                          "is_active": True, "is_verified": True},
            )
            user.set_password(demo.DEMO_STAFF_PASSWORD)
            user.save(update_fields=["password"])
        return len(demo.STAFF_ACCOUNTS)

    def categories(self, kind, rows):
        return {
            slug: Category.objects.update_or_create(
                kind=kind, slug=slug, defaults={"name_fr": fr, "name_en": en, "order": order},
            )[0]
            for order, (slug, fr, en) in enumerate(rows)
        }

    def cover(self, obj, field, filename):
        """Photo depuis les fixtures, seulement si absente."""
        if filename and not getattr(obj, field):
            with open(FIXTURES / filename, "rb") as handle:
                getattr(obj, field).save(filename, File(handle), save=True)

    def offers(self):
        """Offres en cours (dates relatives au jour du chargement)."""
        today = timezone.localdate()
        targets = {"tour": Tour, "hotel": Hotel, "residence": Residence, "vehicle": Vehicle, "activity": Activity}
        for item in demo.OFFERS:
            target = {}
            if item["target"]:
                field, slug = item["target"]
                target = {field: targets[field].objects.get(slug=slug)}
            offer, _ = Offer.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    **translated("title", item["title"]),
                    **translated("short_description", item["short"]),
                    **translated("description", item["description"]),
                    **translated("conditions", item["conditions"]),
                    **translated("cover_alt", item["title"]),
                    "offer_type": item["type"], "badge": item["badge"],
                    "initial_price": demo.price(item["initial"]), "promo_price": demo.price(item["promo"]),
                    "seats_available": item["seats"],
                    "start_date": today - timedelta(days=item["started_days_ago"]),
                    "end_date": today + timedelta(days=item["ends_in_days"]),
                    "destination": Destination.objects.get(slug=item["destination"]),
                    "is_active": True, **target,
                },
            )
            self.cover(offer, "cover_image", item["cover"])
        return len(demo.OFFERS)

    def transports(self):
        for item in demo.TRANSPORTS:
            service, _ = TransportService.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    **translated("title", item["title"]),
                    **translated("description", item["description"]),
                    **translated("schedule_info", item["schedule"]),
                    **translated("cover_alt", item["title"]),
                    "transport_type": item["type"], "origin": item["origin"],
                    "destination": item["destination"], "max_passengers": item["passengers"],
                    "price_from": demo.price(item["price"]), "is_published": True,
                },
            )
            self.cover(service, "cover_image", item["cover"])
        return len(demo.TRANSPORTS)

    def albums(self):
        categories = self.categories(Category.Kind.MEDIA, demo.MEDIA_CATEGORIES)
        today = timezone.localdate()
        for item in demo.ALBUMS:
            album, _ = MediaAlbum.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    **translated("title", item["title"]),
                    **translated("description", item["description"]),
                    "category": categories[item["category"]],
                    "tour": Tour.objects.get(slug=item["tour"]) if item["tour"] else None,
                    "published_at": today - timedelta(days=item["published_days_ago"]),
                    "is_published": True,
                },
            )
            self.cover(album, "cover", item["photos"][0])
            if not album.items.exists():
                for order, filename in enumerate(item["photos"]):
                    photo = MediaItem(album=album, type=MediaItem.Type.PHOTO, order=order,
                                      **translated("alt_text", item["title"]))
                    with open(FIXTURES / filename, "rb") as handle:
                        photo.image.save(filename, File(handle), save=False)
                    photo.save()
        return len(demo.ALBUMS)

    def posts(self):
        categories = self.categories(Category.Kind.BLOG, demo.BLOG_CATEGORIES)
        now = timezone.now()
        for item in demo.BLOG_POSTS:
            post, _ = BlogPost.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    **translated("title", item["title"]),
                    **translated("excerpt", item["excerpt"]),
                    **translated("content", item["content"]),
                    **translated("cover_alt", item["title"]),
                    "category": categories[item["category"]],
                    "status": BlogPost.Status.PUBLIE,
                    "published_at": now - timedelta(days=item["published_days_ago"]),
                },
            )
            post.tags.set([
                Tag.objects.update_or_create(slug=slug, defaults={"name_fr": fr, "name_en": en})[0]
                for slug, fr, en in item["tags"]
            ])
            self.cover(post, "cover_image", item["cover"])
        return len(demo.BLOG_POSTS)

    def quotes(self):
        """Demandes de devis fictives, recréées à chaque chargement (référence et jeton fixes)."""
        QuoteRequest.all_objects.filter(email=demo.DEMO_EMAIL).delete()
        today = timezone.localdate()
        for item in demo.QUOTES:
            departure = today + timedelta(days=item["departure_in_days"])
            proposal = item["proposal"] or {}
            QuoteRequest.objects.create(
                reference=item["reference"], access_token=uuid.UUID(item["token"]),
                first_name=item["first_name"], last_name=item["last_name"],
                email=demo.DEMO_EMAIL, phone=item["phone"], country_code="CI",
                destination=Destination.objects.get(slug=item["destination"]),
                source_tour=Tour.objects.filter(slug=item["tour"]).first() if item["tour"] else None,
                date_departure=departure, date_return=departure + timedelta(days=item["nights"]),
                adults=item["adults"], children=item["children"],
                services_requested=item["services"], comments=item["comments"],
                status=item["status"], consent_at=timezone.now(),
                proposal_amount=demo.price(proposal.get("amount")),
                proposal_message=proposal.get("message", ""),
                proposal_sent_at=timezone.now() if proposal else None,
                proposal_valid_until=today + timedelta(days=proposal["valid_in_days"]) if proposal else None,
            )
        return len(demo.QUOTES)

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
        """Réservations fictives (confirmées, et une demande à lien fixe), recréées à chaque chargement."""
        Booking.all_objects.filter(contact_email=demo.DEMO_EMAIL).delete()
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
        for item in demo.BOOKING_REQUESTS:
            residence = Residence.objects.get(slug=item["residence"])
            total = residence.base_price * item["nights"]
            booking = Booking.objects.create(
                reference=item["reference"], access_token=uuid.UUID(item["token"]),
                contact_name=item["contact_name"], contact_email=demo.DEMO_EMAIL,
                contact_phone=item["phone"], customer_comments=item["comments"],
                status=Booking.Status.REQUESTED, total_amount=total, consent_at=timezone.now(),
            )
            start = today + timedelta(days=item["in_days"])
            BookingItem.objects.create(
                booking=booking, residence=residence,
                label=f"{residence.name} ({item['nights']} nuit(s))",
                unit_price=residence.base_price, line_total=total,
                start_date=start, end_date=start + timedelta(days=item["nights"]),
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
            # Dates relatives : un chargement un autre jour remplace les départs précédents
            # (sauf ceux qu'une réservation protège) au lieu de s'y ajouter.
            starts = [today + timedelta(weeks=weeks) for weeks, *_ in item["departures"]]
            tour.departures.exclude(start_date__in=starts).filter(booking_items__isnull=True).delete()
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
