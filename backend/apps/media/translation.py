"""Champs traduits (FR/EN) — django-modeltranslation, architecture § 12."""
from modeltranslation.translator import TranslationOptions, register

from .models import MediaAlbum, MediaItem


@register(MediaAlbum)
class MediaAlbumTranslationOptions(TranslationOptions):
    fields = ("title", "description")


@register(MediaItem)
class MediaItemTranslationOptions(TranslationOptions):
    fields = ("title", "alt_text")
