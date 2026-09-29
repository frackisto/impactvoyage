from django.contrib import admin

from apps.core.admin import CoverPreviewMixin, GalleryInline, PublishableAdminMixin, TranslatedAdmin

from .models import Destination, DestinationImage


class DestinationImageInline(GalleryInline):
    model = DestinationImage


@admin.register(Destination)
class DestinationAdmin(CoverPreviewMixin, PublishableAdminMixin, TranslatedAdmin):
    list_display = ("cover_preview", "name", "continent", "country_code", "city",
                    "is_published", "is_featured", "views")
    list_display_links = ("cover_preview", "name")
    list_filter = ("continent", "is_published", "is_featured")
    search_fields = ("name", "city", "country_code")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("tags",)
    readonly_fields = ("views", "created", "updated")
    inlines = (DestinationImageInline,)
    fieldsets = (
        (None, {"fields": ("name", "slug", "continent", "country_code", "city",
                           "is_published", "is_featured")}),
        ("Présentation", {"fields": ("short_description", "description", "best_period",
                                     "attractions", "tips", "tags")}),
        ("Image principale", {"fields": ("cover_image", "cover_alt")}),
        ("Statistiques", {"fields": ("views", "created", "updated")}),
    )
