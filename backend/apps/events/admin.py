from django.contrib import admin

from apps.core.admin import CoverPreviewMixin, MediaAssetInline, PublishableAdminMixin, TranslatedAdmin

from .models import Event, EventImage


class EventImageInline(MediaAssetInline):
    model = EventImage


@admin.register(Event)
class EventAdmin(CoverPreviewMixin, PublishableAdminMixin, TranslatedAdmin):
    list_display = ("cover_preview", "title", "category", "date", "location",
                    "participants_count", "is_published", "is_featured")
    list_display_links = ("cover_preview", "title")
    list_filter = ("category", "is_published", "is_featured")
    search_fields = ("title", "location")
    date_hierarchy = "date"
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("destination",)
    readonly_fields = ("created", "updated")
    inlines = (EventImageInline,)
    fieldsets = (
        (None, {"fields": ("title", "slug", "category", "date", "end_date", "location",
                           "destination", "is_published", "is_featured")}),
        ("Présentation", {"fields": ("short_description", "description", "participants_count",
                                     "partners")}),
        ("Image principale", {"fields": ("cover_image", "cover_alt")}),
        ("Historique", {"fields": ("created", "updated")}),
    )
