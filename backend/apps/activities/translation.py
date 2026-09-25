"""Champs traduits (FR/EN) — django-modeltranslation, architecture § 12."""
from modeltranslation.translator import TranslationOptions, register

from .models import Activity, ActivityImage


@register(Activity)
class ActivityTranslationOptions(TranslationOptions):
    fields = ("title", "short_description", "description", "cover_alt")


@register(ActivityImage)
class ActivityImageTranslationOptions(TranslationOptions):
    fields = ("alt_text",)
