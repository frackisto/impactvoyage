"""Champs traduits (FR/EN) — django-modeltranslation, architecture § 12."""
from modeltranslation.translator import TranslationOptions, register

from .models import Category, Tag, SiteSettings


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Tag)
class TagTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(SiteSettings)
class SiteSettingsTranslationOptions(TranslationOptions):
    fields = ("slogan", "hero_subtitle", "opening_hours", "about_content")
