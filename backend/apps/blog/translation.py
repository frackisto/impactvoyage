"""Champs traduits (FR/EN) — django-modeltranslation, architecture § 12."""
from modeltranslation.translator import TranslationOptions, register

from .models import BlogPost


@register(BlogPost)
class BlogPostTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "excerpt",
        "content",
        "seo_title",
        "seo_description",
        "cover_alt",
    )
