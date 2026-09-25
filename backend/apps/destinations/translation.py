"""Champs traduits (FR/EN) — django-modeltranslation, architecture § 12."""
from modeltranslation.translator import TranslationOptions, register

from .models import Destination, DestinationImage


@register(Destination)
class DestinationTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "city",
        "short_description",
        "description",
        "best_period",
        "attractions",
        "tips",
        "cover_alt",
    )


@register(DestinationImage)
class DestinationImageTranslationOptions(TranslationOptions):
    fields = ("alt_text",)
