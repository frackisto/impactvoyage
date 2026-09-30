"""Champs traduits (FR/EN) — django-modeltranslation, architecture § 12."""
from modeltranslation.translator import TranslationOptions, register

from .models import Amenity, Hotel, HotelImage, Residence, ResidenceImage, Room


@register(Amenity)
class AmenityTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Hotel)
class HotelTranslationOptions(TranslationOptions):
    fields = ("short_description", "description", "cover_alt")


@register(HotelImage)
class HotelImageTranslationOptions(TranslationOptions):
    fields = ("alt_text",)


@register(Room)
class RoomTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(Residence)
class ResidenceTranslationOptions(TranslationOptions):
    fields = (
        "short_description",
        "description",
        "services",
        "conditions",
        "cover_alt",
    )


@register(ResidenceImage)
class ResidenceImageTranslationOptions(TranslationOptions):
    fields = ("alt_text",)
