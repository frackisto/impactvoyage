"""Champs traduits (FR/EN) — django-modeltranslation, architecture § 12."""
from modeltranslation.translator import TranslationOptions, register

from .models import Vehicle, VehicleImage


@register(Vehicle)
class VehicleTranslationOptions(TranslationOptions):
    fields = ("description", "cover_alt")


@register(VehicleImage)
class VehicleImageTranslationOptions(TranslationOptions):
    fields = ("alt_text",)
