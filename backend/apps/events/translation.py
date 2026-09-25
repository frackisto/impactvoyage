"""Champs traduits (FR/EN) — django-modeltranslation, architecture § 12."""
from modeltranslation.translator import TranslationOptions, register

from .models import Event, EventImage


@register(Event)
class EventTranslationOptions(TranslationOptions):
    fields = ("title", "short_description", "description", "location", "cover_alt")


@register(EventImage)
class EventImageTranslationOptions(TranslationOptions):
    fields = ("alt_text",)
