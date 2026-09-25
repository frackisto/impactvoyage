"""Champs traduits (FR/EN) — django-modeltranslation, architecture § 12."""
from modeltranslation.translator import TranslationOptions, register

from .models import TransportService


@register(TransportService)
class TransportServiceTranslationOptions(TranslationOptions):
    fields = ("title", "description", "schedule_info", "cover_alt")
