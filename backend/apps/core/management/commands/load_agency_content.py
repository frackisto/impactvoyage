"""
Charge le contenu réel de l'agence (apps/core/agency_content.py) :
paramètres du site, services et tarifs, thèmes de circuits, destinations, visas,
studio meublé, véhicules (non publiés, à compléter) et événements.

    python manage.py load_agency_content          # crée ou met à jour les textes
    python manage.py load_agency_content --force  # remplace aussi les photos existantes

Idempotent : relancer la commande ne crée pas de doublons.
"""
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accommodations.models import Amenity, Residence, ResidenceImage
from apps.core import agency_content as content
from apps.core.models import Category, SiteSettings
from apps.destinations.models import Destination, DestinationImage
from apps.events.models import Event, EventImage
from apps.services.models import Service, ServicePrice
from apps.vehicles.models import Vehicle, VehicleImage
from apps.visas.models import VisaService

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "agency"


class Command(BaseCommand):
    help = "Charge le contenu réel de l'agence repris de l'ancien site impact-voyage.com."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Remplace les photos déjà présentes.")

    def set_image(self, field, filename):
        """Attache une photo des fixtures si le champ est vide (ou avec --force)."""
        if not filename or (field and not self.force):
            return False
        with open(FIXTURES / filename, "rb") as handle:
            field.save(filename, File(handle), save=False)
        return True

    def gallery(self, model, owner_field, owner, filenames, alt):
        if getattr(owner, "images" if model is not EventImage else "media").exists() and not self.force:
            return
        getattr(owner, "images" if model is not EventImage else "media").all().delete()
        for order, filename in enumerate(filenames):
            item = model(**{owner_field: owner}, alt_text=alt, order=order)
            if model is EventImage:
                item.type = EventImage.Type.PHOTO
            with open(FIXTURES / filename, "rb") as handle:
                item.image.save(filename, File(handle), save=False)
            item.save()

    @transaction.atomic
    def handle(self, *args, force=False, **options):
        self.force = force
        self.site_settings()
        themes = self.tour_themes()
        services = self.services()
        destinations = self.destinations()
        visas = self.visas()
        self.residence(destinations)
        vehicles = self.vehicles()
        events = self.events(destinations)
        self.stdout.write(self.style.SUCCESS(
            f"Contenu chargé : {themes} thèmes, {services} services, {destinations and len(destinations)} "
            f"destinations, {visas} visas, 1 résidence, {vehicles} véhicules (non publiés), "
            f"{events} événements."
        ))

    def site_settings(self):
        data = dict(content.SITE_SETTINGS)
        hero = data.pop("hero_image")
        settings = SiteSettings.load()
        for key, value in data.items():
            setattr(settings, key, value)
        self.set_image(settings.hero_image, hero)
        settings.save()

    def tour_themes(self):
        for order, (slug, fr, en) in enumerate(content.TOUR_THEMES):
            Category.objects.update_or_create(
                kind=Category.Kind.TOUR_THEME, slug=slug,
                defaults={"name_fr": fr, "name_en": en, "order": order},
            )
        return len(content.TOUR_THEMES)

    def services(self):
        for order, (slug, title_fr, title_en, desc_fr, desc_en, icon, quote_type, prices) in enumerate(
            content.SERVICES
        ):
            service, _ = Service.objects.update_or_create(
                slug=slug,
                defaults={
                    "title_fr": title_fr, "title_en": title_en,
                    "short_description_fr": desc_fr, "short_description_en": desc_en,
                    "icon": icon, "quote_service_type": quote_type, "order": order,
                    "is_published": True,
                },
            )
            service.prices.all().delete()
            ServicePrice.objects.bulk_create([
                ServicePrice(
                    service=service, label_fr=label_fr, label_en=label_en,
                    label=label_fr, price=price, unit_fr=unit_fr, unit_en=unit_en, unit=unit_fr,
                    order=index,
                )
                for index, (label_fr, label_en, price, unit_fr, unit_en) in enumerate(prices)
            ])
        return len(content.SERVICES)

    def destinations(self):
        result = {}
        for (slug, name_fr, name_en, continent, country, city_fr, city_en, short_fr, short_en,
             desc_fr, desc_en, cover, gallery, featured) in content.DESTINATIONS:
            destination, _ = Destination.objects.update_or_create(
                slug=slug,
                defaults={
                    "name_fr": name_fr, "name_en": name_en, "continent": continent,
                    "country_code": country, "city_fr": city_fr, "city_en": city_en,
                    "short_description_fr": short_fr, "short_description_en": short_en,
                    "description_fr": desc_fr, "description_en": desc_en,
                    "cover_alt_fr": name_fr, "cover_alt_en": name_en,
                    "is_featured": featured, "is_published": True,
                },
            )
            if self.set_image(destination.cover_image, cover):
                destination.save()
            self.gallery(DestinationImage, "destination", destination, gallery, name_fr)
            result[slug] = destination
        return result

    def visas(self):
        desc_fr, desc_en = content.VISA_DESCRIPTION
        for code, slug, type_fr, type_en, fees in content.VISAS:
            VisaService.objects.update_or_create(
                destination_country_code=code, nationality_code="CI",
                visa_type=type_fr, purpose=VisaService.Purpose.TOURISME,
                defaults={
                    "country_slug": slug, "visa_type_fr": type_fr, "visa_type_en": type_en,
                    "fees": fees, "description_fr": desc_fr, "description_en": desc_en,
                    "is_published": True,
                },
            )
        return len(content.VISAS)

    def residence(self, destinations):
        data = content.RESIDENCE
        residence, _ = Residence.objects.update_or_create(
            slug=data["slug"],
            defaults={
                "name": data["name"],
                "destination": destinations[data["destination"]], "address": data["address"],
                "rooms_count": data["rooms_count"], "capacity": data["capacity"],
                "base_price": data["base_price"],
                "short_description_fr": data["short_description_fr"],
                "short_description_en": data["short_description_en"],
                "description_fr": data["description_fr"], "description_en": data["description_en"],
                "conditions_fr": data["conditions_fr"], "conditions_en": data["conditions_en"],
                "cover_alt_fr": data["name"], "is_published": True, "is_featured": True,
            },
        )
        amenities = []
        for name_fr, name_en, icon in data["amenities"]:
            amenity, _ = Amenity.objects.update_or_create(
                name_fr=name_fr,
                defaults={"name": name_fr, "name_en": name_en, "icon": icon,
                          "scope": Amenity.Scope.BOTH},
            )
            amenities.append(amenity)
        residence.amenities.set(amenities)
        if self.set_image(residence.cover_image, data["cover"]):
            residence.save()
        self.gallery(ResidenceImage, "residence", residence, data["gallery"], data["name"])

    def vehicles(self):
        for slug, brand, model, category, seats, cover, gallery in content.VEHICLES:
            vehicle, created = Vehicle.objects.get_or_create(
                slug=slug,
                defaults={
                    "brand": brand, "model": model, "category": category, "seats": seats,
                    "year": 2024, "plate_number": f"A-COMPLETER-{slug}"[:20],
                    "transmission": Vehicle.Transmission.MANUELLE, "fuel": Vehicle.Fuel.ESSENCE,
                    "base_price": 0,
                    "description_fr": "À COMPLÉTER : année, prix par jour, immatriculation, "
                                      "boîte de vitesses et carburant, puis publier la fiche.",
                    "cover_alt_fr": f"{brand} {model}",
                    # Informations incomplètes : jamais publié automatiquement.
                    "is_published": False,
                },
            )
            if self.set_image(vehicle.cover_image, cover):
                vehicle.save()
            self.gallery(VehicleImage, "vehicle", vehicle, gallery, f"{brand} {model}")
        return len(content.VEHICLES)

    def events(self, destinations):
        for (slug, title_fr, title_en, category, day, location, destination, desc_fr, desc_en,
             cover, gallery) in content.EVENTS:
            complete = "COMPLÉTER" not in desc_fr
            event, _ = Event.objects.update_or_create(
                slug=slug,
                defaults={
                    "title_fr": title_fr, "title_en": title_en, "category": category,
                    "date": day, "location_fr": location, "location": location,
                    "destination": destinations.get(destination),
                    "short_description_fr": desc_fr, "short_description_en": desc_en,
                    "description_fr": desc_fr, "description_en": desc_en,
                    "cover_alt_fr": title_fr, "cover_alt_en": title_en,
                    "is_published": complete, "is_featured": complete,
                },
            )
            if self.set_image(event.cover_image, cover):
                event.save()
            self.gallery(EventImage, "event", event, gallery, title_fr)
        return len(content.EVENTS)
