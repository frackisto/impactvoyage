"""Champs traduits (FR/EN) — django-modeltranslation, architecture § 12."""
from modeltranslation.translator import TranslationOptions, register

from .models import Service


@register(Service)
class ServiceTranslationOptions(TranslationOptions):
    fields = ("title", "short_description", "description")
