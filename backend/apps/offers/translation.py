"""Champs traduits (FR/EN) — django-modeltranslation, architecture § 12."""
from modeltranslation.translator import TranslationOptions, register

from .models import Offer


@register(Offer)
class OfferTranslationOptions(TranslationOptions):
    fields = ("title", "short_description", "description", "conditions", "cover_alt")
