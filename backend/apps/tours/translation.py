"""Champs traduits (FR/EN) — django-modeltranslation, architecture § 12."""
from modeltranslation.translator import TranslationOptions, register

from .models import Tour, TourDay, TourImage


@register(Tour)
class TourTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "short_description",
        "description",
        "departure_points",
        "transport_info",
        "accommodation_info",
        "inclusions",
        "exclusions",
        "conditions",
        "cover_alt",
    )


@register(TourImage)
class TourImageTranslationOptions(TranslationOptions):
    fields = ("alt_text",)


@register(TourDay)
class TourDayTranslationOptions(TranslationOptions):
    fields = ("title", "description")
