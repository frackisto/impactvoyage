"""Champs traduits (FR/EN) — django-modeltranslation, architecture § 12."""
from modeltranslation.translator import TranslationOptions, register

from .models import VisaService


@register(VisaService)
class VisaServiceTranslationOptions(TranslationOptions):
    fields = (
        "visa_type",
        "validity_duration",
        "processing_time",
        "required_documents",
        "description",
    )
